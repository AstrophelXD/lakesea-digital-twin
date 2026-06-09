import asyncio
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.ws_manager import ws_manager
from app.models.constants import (
    ALARM_DATA_SPIKE,
    ALARM_LOW_BATTERY,
    ALARM_NEAR_BOUNDARY,
    ALARM_OUT_OF_BOUNDARY,
    ALARM_SPEED_LIMIT,
    BOUNDARY_MARGIN,
    LOW_BATTERY_THRESHOLD,
    POOL_HEIGHT,
    POOL_WIDTH,
    RUNNING,
    SPEED_LIMIT,
)
from app.models.monitor import AlarmRecord, SensorData, ShipTrack
from app.repositories.alarm_repository import AlarmRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.sensor_repository import SensorRepository
from app.schemas.monitor_schema import MonitorFrame, MonitorSnapshotOut, MonitorStatusOut, SensorPointOut, TrackPointOut


@dataclass
class SimState:
    x: float = 10.0
    y: float = 10.0
    heading: float = 45.0
    speed: float = 1.5
    roll: float = 0.0
    pitch: float = 0.0
    battery: float = 100.0
    resistance: float = 30.0
    frame_count: int = 0
    prev_resistance: float = 30.0


@dataclass
class SimRunner:
    experiment_id: int
    state: SimState = field(default_factory=SimState)
    task: Optional[asyncio.Task] = None
    running: bool = False


class MonitorService:
    _runners: dict[int, SimRunner] = {}
    _tick_interval: float = 1.0
    _alarm_cooldown_sec: int = 15

    def __init__(self, db: Session) -> None:
        self.db = db
        self.experiment_repo = ExperimentRepository(db)

    @classmethod
    def get_runner(cls, experiment_id: int) -> SimRunner:
        if experiment_id not in cls._runners:
            cls._runners[experiment_id] = SimRunner(experiment_id=experiment_id)
        return cls._runners[experiment_id]

    def _ensure_running_task(self, experiment_id: int) -> None:
        task = self.experiment_repo.get_by_id(experiment_id)
        if not task:
            raise HTTPException(status_code=404, detail="试验任务不存在")
        if task.status != RUNNING:
            raise HTTPException(status_code=400, detail="仅执行中的试验可开启实时监控")

    def get_status(self, experiment_id: int) -> MonitorStatusOut:
        settings = get_settings()
        runner = self.get_runner(experiment_id)
        mqtt_connected = None
        if settings.enable_mqtt:
            from app.services.mqtt_service import mqtt_service

            mqtt_connected = mqtt_service.is_connected
        return MonitorStatusOut(
            experiment_id=experiment_id,
            running=runner.running,
            connected_clients=ws_manager.client_count(experiment_id),
            frame_count=runner.state.frame_count,
            data_source="mqtt" if settings.enable_mqtt else "websocket_sim",
            mqtt_connected=mqtt_connected,
        )

    async def start_simulation(self, experiment_id: int) -> MonitorStatusOut:
        self._ensure_running_task(experiment_id)
        runner = self.get_runner(experiment_id)
        if runner.running:
            return self.get_status(experiment_id)
        runner.running = True
        if not get_settings().enable_mqtt:
            runner.task = asyncio.create_task(self._simulation_loop(experiment_id))
        return self.get_status(experiment_id)

    async def stop_simulation(self, experiment_id: int) -> MonitorStatusOut:
        runner = self.get_runner(experiment_id)
        runner.running = False
        if runner.task and not runner.task.done():
            runner.task.cancel()
            try:
                await runner.task
            except asyncio.CancelledError:
                pass
        runner.task = None
        return self.get_status(experiment_id)

    @classmethod
    def request_stop(cls, experiment_id: int) -> None:
        runner = cls._runners.get(experiment_id)
        if not runner or not runner.running:
            return
        runner.running = False
        if runner.task and not runner.task.done():
            runner.task.cancel()

    @classmethod
    async def stop_if_running(cls, experiment_id: int) -> None:
        cls.request_stop(experiment_id)
        runner = cls._runners.get(experiment_id)
        if runner and runner.task:
            try:
                await runner.task
            except asyncio.CancelledError:
                pass
            runner.task = None

    async def _simulation_loop(self, experiment_id: int) -> None:
        runner = self.get_runner(experiment_id)
        try:
            while runner.running:
                frame = self._generate_frame(experiment_id, runner.state)
                await ws_manager.broadcast(experiment_id, frame)
                await asyncio.to_thread(self.persist_frame, experiment_id, frame)
                await asyncio.sleep(self._tick_interval)
        except asyncio.CancelledError:
            runner.running = False
            raise

    def _generate_frame(self, experiment_id: int, state: SimState) -> dict[str, Any]:
        state.frame_count += 1
        rad = math.radians(state.heading)
        state.x += state.speed * 0.5 * math.cos(rad) + random.uniform(-0.1, 0.1)
        state.y += state.speed * 0.5 * math.sin(rad) + random.uniform(-0.1, 0.1)

        if state.x <= 0 or state.x >= POOL_WIDTH:
            state.heading = (180 - state.heading) % 360
            state.x = max(0.5, min(POOL_WIDTH - 0.5, state.x))
        if state.y <= 0 or state.y >= POOL_HEIGHT:
            state.heading = (-state.heading) % 360
            state.y = max(0.5, min(POOL_HEIGHT - 0.5, state.y))

        state.heading = (state.heading + random.uniform(-8, 8)) % 360
        state.speed = max(0.5, min(3.5, state.speed + random.uniform(-0.15, 0.15)))
        state.roll = max(-25, min(25, state.roll + random.uniform(-2, 2)))
        state.pitch = max(-15, min(15, state.pitch + random.uniform(-1, 1)))
        state.battery = max(5, state.battery - random.uniform(0.3, 0.8))
        state.resistance = max(10, min(60, state.resistance + random.uniform(-3, 3)))

        if state.frame_count > 30 and random.random() < 0.02:
            state.battery = min(state.battery, random.uniform(8, 18))

        now = datetime.now()
        alarm_payload = self._evaluate_alarms(experiment_id, state, now)

        frame = MonitorFrame(
            experiment_id=experiment_id,
            ship_code="M-001",
            timestamp=now.strftime("%Y-%m-%d %H:%M:%S"),
            position={"x": round(state.x, 2), "y": round(state.y, 2)},
            speed=round(state.speed, 2),
            heading=round(state.heading, 2),
            roll=round(state.roll, 2),
            pitch=round(state.pitch, 2),
            battery=round(state.battery, 2),
            resistance=round(state.resistance, 2),
            alarm=alarm_payload,
        )
        state.prev_resistance = state.resistance
        return frame.model_dump(by_alias=True)

    def _evaluate_alarms(
        self, experiment_id: int, state: SimState, now: datetime
    ) -> Optional[dict[str, Any]]:
        cooldown = now - timedelta(seconds=self._alarm_cooldown_sec)
        checks: list[tuple[str, str, str, bool]] = []

        out = (
            state.x < 0
            or state.x > POOL_WIDTH
            or state.y < 0
            or state.y > POOL_HEIGHT
        )
        near = (
            state.x < BOUNDARY_MARGIN
            or state.x > POOL_WIDTH - BOUNDARY_MARGIN
            or state.y < BOUNDARY_MARGIN
            or state.y > POOL_HEIGHT - BOUNDARY_MARGIN
        )
        if out:
            checks.append((ALARM_OUT_OF_BOUNDARY, "HIGH", "模型船越界", True))
        elif near:
            checks.append((ALARM_NEAR_BOUNDARY, "MEDIUM", "模型船接近边界", True))

        if state.battery < LOW_BATTERY_THRESHOLD:
            checks.append((ALARM_LOW_BATTERY, "HIGH", f"电池电量过低 ({state.battery:.0f}%)", True))

        if state.speed > SPEED_LIMIT:
            checks.append(
                (ALARM_SPEED_LIMIT, "MEDIUM", f"速度超过阈值 ({state.speed:.1f} m/s)", True)
            )

        if abs(state.resistance - state.prev_resistance) > 15:
            checks.append((ALARM_DATA_SPIKE, "MEDIUM", "阻力数据突变", True))

        db = SessionLocal()
        try:
            alarm_repo = AlarmRepository(db)
            for alarm_type, level, message, _ in checks:
                if alarm_repo.has_recent_alarm(experiment_id, alarm_type, cooldown):
                    continue
                record = alarm_repo.create(
                    AlarmRecord(
                        experiment_id=experiment_id,
                        alarm_type=alarm_type,
                        alarm_level=level,
                        alarm_message=message,
                        handle_status="PENDING",
                    )
                )
                db.commit()
                return {
                    "id": record.id,
                    "type": alarm_type,
                    "level": level,
                    "message": message,
                }
        finally:
            db.close()
        return None

    @staticmethod
    def persist_frame(experiment_id: int, frame: dict[str, Any]) -> None:
        db = SessionLocal()
        try:
            repo = SensorRepository(db)
            ts = datetime.strptime(frame["timestamp"], "%Y-%m-%d %H:%M:%S")
            pos = frame["position"]
            repo.add_sensor_row(
                SensorData(
                    experiment_id=experiment_id,
                    timestamp=ts,
                    position_x=Decimal(str(pos["x"])),
                    position_y=Decimal(str(pos["y"])),
                    speed=Decimal(str(frame["speed"])),
                    heading=Decimal(str(frame["heading"])),
                    roll=Decimal(str(frame["roll"])),
                    pitch=Decimal(str(frame["pitch"])),
                    battery=Decimal(str(frame["battery"])),
                    resistance=Decimal(str(frame["resistance"])),
                )
            )
            repo.add_track_row(
                ShipTrack(
                    experiment_id=experiment_id,
                    timestamp=ts,
                    position_x=Decimal(str(pos["x"])),
                    position_y=Decimal(str(pos["y"])),
                    heading=Decimal(str(frame["heading"])),
                )
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    async def trigger_demo_alarm(
        self, experiment_id: int, alarm_type: str
    ) -> dict[str, Any]:
        self._ensure_running_task(experiment_id)
        runner = self.get_runner(experiment_id)
        state = runner.state
        mapping = {
            "LOW_BATTERY": (ALARM_LOW_BATTERY, "HIGH", "演示：电池电量过低"),
            "OUT_OF_BOUNDARY": (ALARM_OUT_OF_BOUNDARY, "HIGH", "演示：模型船越界"),
            "DATA_SPIKE": (ALARM_DATA_SPIKE, "MEDIUM", "演示：传感器数据突变"),
        }
        if alarm_type not in mapping:
            raise HTTPException(status_code=400, detail="不支持的告警类型")
        atype, level, message = mapping[alarm_type]
        if alarm_type == "LOW_BATTERY":
            state.battery = 12.0
        elif alarm_type == "OUT_OF_BOUNDARY":
            state.x = POOL_WIDTH + 1
        elif alarm_type == "DATA_SPIKE":
            state.resistance = state.prev_resistance + 25

        record = AlarmRepository(self.db).create(
            AlarmRecord(
                experiment_id=experiment_id,
                alarm_type=atype,
                alarm_level=level,
                alarm_message=message,
                handle_status="PENDING",
            )
        )
        self.db.commit()
        frame = self._generate_frame(experiment_id, state)
        frame["alarm"] = {
            "id": record.id,
            "type": atype,
            "level": level,
            "message": message,
        }
        await ws_manager.broadcast(experiment_id, frame)
        return frame

    def get_snapshot(self, experiment_id: int) -> MonitorSnapshotOut:
        sensor_repo = SensorRepository(self.db)
        tracks = sensor_repo.list_tracks(experiment_id, 200)
        sensors = sensor_repo.list_recent_sensor(experiment_id, 50)

        latest: Optional[MonitorFrame] = None
        if sensors:
            s = sensors[-1]
            latest = MonitorFrame(
                experiment_id=experiment_id,
                timestamp=s.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                position={
                    "x": float(s.position_x or 0),
                    "y": float(s.position_y or 0),
                },
                speed=float(s.speed or 0),
                heading=float(s.heading or 0),
                roll=float(s.roll or 0),
                pitch=float(s.pitch or 0),
                battery=float(s.battery or 0),
                resistance=float(s.resistance or 0),
            )

        return MonitorSnapshotOut(
            latest=latest,
            tracks=[
                TrackPointOut(
                    timestamp=t.timestamp,
                    position_x=float(t.position_x) if t.position_x else None,
                    position_y=float(t.position_y) if t.position_y else None,
                    heading=float(t.heading) if t.heading else None,
                )
                for t in tracks
            ],
            recent_sensor=[
                SensorPointOut(
                    timestamp=s.timestamp,
                    position_x=float(s.position_x) if s.position_x else None,
                    position_y=float(s.position_y) if s.position_y else None,
                    speed=float(s.speed) if s.speed else None,
                    battery=float(s.battery) if s.battery else None,
                    resistance=float(s.resistance) if s.resistance else None,
                )
                for s in sensors
            ],
        )
