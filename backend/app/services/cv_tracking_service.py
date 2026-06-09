import asyncio
import json
import math
import random
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.ws_manager import ws_manager
from app.models.constants import POOL_HEIGHT, POOL_WIDTH
from app.models.monitor import ShipTrack
from app.repositories.sensor_repository import SensorRepository
from app.schemas.cv_schema import CvTrackResult, CvTrackStatusOut

try:
    import cv2
    import numpy as np

    OPENCV_AVAILABLE = True
except ImportError:
    cv2 = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]
    OPENCV_AVAILABLE = False


class CvTrackingService:
    _trackers: dict[int, bool] = {}
    _latest: dict[int, CvTrackResult] = {}
    _tasks: dict[int, asyncio.Task] = {}
    _frame_index: dict[int, int] = {}

    POOL_W_PX = 640
    POOL_H_PX = 360

    @classmethod
    def is_opencv_available(cls) -> bool:
        return OPENCV_AVAILABLE

    @classmethod
    def is_tracking(cls, experiment_id: int) -> bool:
        return cls._trackers.get(experiment_id, False)

    @classmethod
    def get_latest(cls, experiment_id: int) -> Optional[CvTrackResult]:
        return cls._latest.get(experiment_id)

    @classmethod
    def get_status(cls, experiment_id: int) -> CvTrackStatusOut:
        return CvTrackStatusOut(
            enabled=True,
            opencv_available=OPENCV_AVAILABLE,
            tracking=cls.is_tracking(experiment_id),
            latest=cls.get_latest(experiment_id),
        )

    @classmethod
    async def start_tracking(cls, experiment_id: int, camera_id: str = "CAM-001") -> CvTrackStatusOut:
        if cls.is_tracking(experiment_id):
            return cls.get_status(experiment_id)
        cls._trackers[experiment_id] = True
        cls._frame_index[experiment_id] = 0
        cls._tasks[experiment_id] = asyncio.create_task(cls._tracking_loop(experiment_id, camera_id))
        return cls.get_status(experiment_id)

    @classmethod
    async def stop_tracking(cls, experiment_id: int) -> CvTrackStatusOut:
        cls._trackers[experiment_id] = False
        task = cls._tasks.pop(experiment_id, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        return cls.get_status(experiment_id)

    @classmethod
    async def _tracking_loop(cls, experiment_id: int, camera_id: str) -> None:
        try:
            while cls._trackers.get(experiment_id):
                idx = cls._frame_index.get(experiment_id, 0)
                result = cls._detect_frame(experiment_id, camera_id, idx)
                cls._frame_index[experiment_id] = idx + 1
                cls._latest[experiment_id] = result
                await asyncio.to_thread(cls._persist_track, experiment_id, result)
                await ws_manager.broadcast(
                    experiment_id,
                    {"type": "cv_track", **result.model_dump(by_alias=True)},
                )
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            cls._trackers[experiment_id] = False
            raise

    @classmethod
    def _detect_frame(cls, experiment_id: int, camera_id: str, frame_index: int) -> CvTrackResult:
        now = datetime.now()
        if OPENCV_AVAILABLE:
            frame = cls._render_demo_frame(frame_index)
            result = cls._detect_color_blob(frame, camera_id, now)
            if result:
                result.experiment_id = experiment_id
                return result

        t = frame_index * 0.05
        pool_x = POOL_WIDTH * (0.3 + 0.4 * (0.5 + 0.5 * math.sin(t)))
        pool_y = POOL_HEIGHT * (0.5 + 0.2 * math.cos(t * 0.7))
        cx = pool_x / POOL_WIDTH * cls.POOL_W_PX
        cy = pool_y / POOL_HEIGHT * cls.POOL_H_PX
        bw, bh = 60, 40
        return CvTrackResult(
            experiment_id=experiment_id,
            camera_id=camera_id,
            timestamp=now.strftime("%Y-%m-%dT%H:%M:%S"),
            bbox=[cx - bw / 2, cy - bh / 2, bw, bh],
            center_x=round(cx, 1),
            center_y=round(cy, 1),
            pool_x=round(pool_x, 2),
            pool_y=round(pool_y, 2),
            confidence=round(0.85 + random.uniform(0, 0.1), 2),
            source="simulation" if not OPENCV_AVAILABLE else "opencv",
        )

    @classmethod
    def _render_demo_frame(cls, frame_index: int):
        w, h = cls.POOL_W_PX, cls.POOL_H_PX
        img = np.full((h, w, 3), (12, 74, 110), dtype=np.uint8)
        t = frame_index * 0.05
        cx = int(w * (0.3 + 0.4 * (0.5 + 0.5 * math.sin(t))))
        cy = int(h * (0.5 + 0.2 * math.cos(t * 0.7)))
        cv2.rectangle(img, (cx - 30, cy - 15), (cx + 30, cy + 15), (0, 200, 255), -1)
        return img

    @classmethod
    def _detect_color_blob(cls, frame, camera_id: str, now: datetime) -> Optional[CvTrackResult]:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower = np.array([85, 80, 80])
        upper = np.array([105, 255, 255])
        mask = cv2.inRange(hsv, lower, upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        cnt = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(cnt)
        if w * h < 100:
            return None
        cx = x + w / 2
        cy = y + h / 2
        pool_x = cx / cls.POOL_W_PX * POOL_WIDTH
        pool_y = (1 - cy / cls.POOL_H_PX) * POOL_HEIGHT
        area = w * h
        confidence = min(0.98, 0.6 + area / 5000)
        return CvTrackResult(
            experiment_id=0,
            camera_id=camera_id,
            timestamp=now.strftime("%Y-%m-%dT%H:%M:%S"),
            bbox=[float(x), float(y), float(w), float(h)],
            center_x=round(cx, 1),
            center_y=round(cy, 1),
            pool_x=round(pool_x, 2),
            pool_y=round(max(0, pool_y), 2),
            confidence=round(confidence, 2),
            source="opencv",
        )

    @staticmethod
    def _persist_track(experiment_id: int, result: CvTrackResult) -> None:
        db = SessionLocal()
        try:
            repo = SensorRepository(db)
            ts = datetime.strptime(result.timestamp[:19], "%Y-%m-%dT%H:%M:%S")
            repo.add_track_row(
                ShipTrack(
                    experiment_id=experiment_id,
                    timestamp=ts,
                    position_x=Decimal(str(result.pool_x)),
                    position_y=Decimal(str(result.pool_y)),
                    heading=Decimal("0"),
                )
            )
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
