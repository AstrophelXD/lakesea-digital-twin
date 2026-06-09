from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.constants import PENDING_PREPARE, READY, RUNNING, TASK_COMPLETED, TASK_ARCHIVED
from app.repositories.alarm_repository import AlarmRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.file_repository import FileRepository
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.sensor_repository import SensorRepository
from app.schemas.alarm_schema import AlarmOut
from app.models.user import SysUser
from app.repositories.ai_repository import AiReportRepository
from app.services.audit_service import AuditService
from app.schemas.archive_schema import (
    AiReportBrief,
    ExperimentFileOut,
    ExperimentReplayOut,
    ReplayAlarmMarker,
    ReplaySensorPoint,
    ReplayStats,
    ReplayTrackPoint,
)
from app.schemas.common import PageResult
from app.schemas.experiment_schema import ExperimentOut


class ExperimentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ExperimentRepository(db)
        self.reservation_repo = ReservationRepository(db)
        self.sensor_repo = SensorRepository(db)
        self.alarm_repo = AlarmRepository(db)
        self.file_repo = FileRepository(db)
        self.ai_repo = AiReportRepository(db)

    def list_tasks(
        self, status: Optional[str] = None, page: int = 1, page_size: int = 20
    ) -> PageResult[ExperimentOut]:
        items, total = self.repo.list_tasks(status, page, page_size)
        return PageResult(
            items=[ExperimentOut.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_task(self, task_id: int) -> ExperimentOut:
        task = self.repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="试验任务不存在")
        return ExperimentOut.model_validate(task)

    def _get_task_or_404(self, task_id: int):
        task = self.repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="试验任务不存在")
        return task

    def mark_ready(self, task_id: int, operator: SysUser) -> ExperimentOut:
        task = self._get_task_or_404(task_id)
        if task.status != PENDING_PREPARE:
            raise HTTPException(status_code=400, detail="仅待准备状态可标记为已准备")
        task.status = READY
        self.db.commit()
        self.db.refresh(task)
        AuditService(self.db).log_user(
            operator,
            "EXPERIMENT",
            "READY",
            target_type="Experiment",
            target_id=task_id,
            detail=task.exp_name,
        )
        return ExperimentOut.model_validate(task)

    def start(self, task_id: int, operator: SysUser) -> ExperimentOut:
        from datetime import datetime

        task = self._get_task_or_404(task_id)
        if task.status != READY:
            raise HTTPException(status_code=400, detail="仅已准备状态可启动试验")
        task.status = RUNNING
        task.actual_start_time = datetime.now()
        self.db.commit()
        self.db.refresh(task)
        AuditService(self.db).log_user(
            operator,
            "EXPERIMENT",
            "START",
            target_type="Experiment",
            target_id=task_id,
            detail=task.exp_name,
        )
        return ExperimentOut.model_validate(task)

    def finish(self, task_id: int, operator: SysUser) -> ExperimentOut:
        from datetime import datetime

        from app.services.monitor_service import MonitorService

        task = self._get_task_or_404(task_id)
        if task.status != RUNNING:
            raise HTTPException(status_code=400, detail="仅执行中状态可完成试验")
        MonitorService.request_stop(task_id)
        task.status = TASK_COMPLETED
        task.actual_end_time = datetime.now()
        reservation = self.reservation_repo.get_by_id(task.reservation_id)
        if reservation:
            reservation.status = "COMPLETED"
        self.db.commit()
        self.db.refresh(task)
        AuditService(self.db).log_user(
            operator,
            "EXPERIMENT",
            "FINISH",
            target_type="Experiment",
            target_id=task_id,
            detail=task.exp_name,
        )
        return ExperimentOut.model_validate(task)

    def archive(self, task_id: int, operator: SysUser) -> ExperimentOut:
        from datetime import datetime

        task = self._get_task_or_404(task_id)
        if task.status != TASK_COMPLETED:
            raise HTTPException(status_code=400, detail="仅已完成状态可归档")
        task.status = TASK_ARCHIVED
        task.archive_time = datetime.now()
        reservation = self.reservation_repo.get_by_id(task.reservation_id)
        if reservation:
            reservation.status = "ARCHIVED"
        self.db.commit()
        self.db.refresh(task)
        AuditService(self.db).log_user(
            operator,
            "EXPERIMENT",
            "ARCHIVE",
            target_type="Experiment",
            target_id=task_id,
            detail=task.exp_name,
        )
        return ExperimentOut.model_validate(task)

    @staticmethod
    def _nearest_series_index(
        series: list, alarm_time
    ) -> int:
        if not series:
            return 0
        best_idx = 0
        best_delta = abs((series[0].timestamp - alarm_time).total_seconds())
        for i, point in enumerate(series):
            delta = abs((point.timestamp - alarm_time).total_seconds())
            if delta < best_delta:
                best_delta = delta
                best_idx = i
        return best_idx

    def get_replay(self, task_id: int) -> ExperimentReplayOut:
        task = self._get_task_or_404(task_id)
        tracks_raw = self.sensor_repo.list_tracks(task_id, 2000)
        sensors_raw = self.sensor_repo.list_sensor_series(task_id, 2000)
        alarms_raw, _ = self.alarm_repo.list_alarms(experiment_id=task_id, page_size=200)
        files_raw = self.file_repo.list_by_experiment(task_id)
        ai_report = self.ai_repo.get_by_experiment(task_id)

        speeds = [float(s.speed) for s in sensors_raw if s.speed is not None]
        batteries = [float(s.battery) for s in sensors_raw if s.battery is not None]
        resistances = [float(s.resistance) for s in sensors_raw if s.resistance is not None]

        alarm_markers = [
            ReplayAlarmMarker(
                alarm_id=a.id,
                alarm_type=a.alarm_type,
                alarm_message=a.alarm_message,
                create_time=a.create_time,
                series_index=self._nearest_series_index(sensors_raw, a.create_time),
            )
            for a in alarms_raw
        ]

        return ExperimentReplayOut(
            task=ExperimentOut.model_validate(task),
            tracks=[
                ReplayTrackPoint(
                    timestamp=t.timestamp,
                    position_x=float(t.position_x or 0),
                    position_y=float(t.position_y or 0),
                    heading=float(t.heading) if t.heading else None,
                )
                for t in tracks_raw
            ],
            sensor_series=[
                ReplaySensorPoint(
                    timestamp=s.timestamp,
                    speed=float(s.speed) if s.speed else None,
                    battery=float(s.battery) if s.battery else None,
                    resistance=float(s.resistance) if s.resistance else None,
                    roll=float(s.roll) if s.roll else None,
                )
                for s in sensors_raw
            ],
            alarms=[AlarmOut.model_validate(a) for a in alarms_raw],
            alarm_markers=alarm_markers,
            files=[ExperimentFileOut.model_validate(f) for f in files_raw],
            stats=ReplayStats(
                point_count=len(sensors_raw),
                max_speed=max(speeds) if speeds else None,
                min_battery=min(batteries) if batteries else None,
                max_resistance=max(resistances) if resistances else None,
                alarm_count=len(alarms_raw),
            ),
            ai_report=AiReportBrief.model_validate(ai_report) if ai_report else None,
        )
