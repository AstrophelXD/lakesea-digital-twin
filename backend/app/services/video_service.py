import math
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import SysUser
from app.models.video_record import VideoRecord
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.video_repository import VideoRepository
from app.schemas.common import PageResult
from app.schemas.video_schema import VideoRecordOut, VideoStreamConfigOut


class VideoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = VideoRepository(db)
        self.experiment_repo = ExperimentRepository(db)

    def _ensure_experiment(self, experiment_id: int) -> None:
        if not self.experiment_repo.get_by_id(experiment_id):
            raise HTTPException(status_code=404, detail="试验任务不存在")

    def _demo_file_path(self) -> Path:
        settings = get_settings()
        upload_path = Path(settings.upload_dir) / "videos" / "demo_pool.mp4"
        if upload_path.exists():
            return upload_path
        assets_path = Path(__file__).resolve().parents[2] / "assets" / "videos" / "demo_pool.mp4"
        if assets_path.exists():
            return assets_path
        upload_path.parent.mkdir(parents=True, exist_ok=True)
        return upload_path

    def get_stream_config(self, experiment_id: int) -> VideoStreamConfigOut:
        self._ensure_experiment(experiment_id)
        settings = get_settings()
        active = self.repo.get_active(experiment_id)
        mode = settings.video_mode
        demo_path = self._demo_file_path()
        file_url = None
        if demo_path.exists():
            file_url = f"/api/video/{experiment_id}/demo-file"
        return VideoStreamConfigOut(
            mode=mode,
            camera_id=settings.video_camera_id,
            stream_url=settings.video_rtsp_url or None,
            file_url=file_url,
            mjpeg_url=f"/api/video/{experiment_id}/mjpeg",
            status=active.status if active else "IDLE",
        )

    def start_recording(
        self, experiment_id: int, camera_id: str, mode: str, operator: SysUser
    ) -> VideoRecordOut:
        self._ensure_experiment(experiment_id)
        now = datetime.now()
        self.repo.stop_active(experiment_id, now)
        demo_path = self._demo_file_path()
        settings = get_settings()
        record = self.repo.create(
            VideoRecord(
                experiment_id=experiment_id,
                camera_id=camera_id or settings.video_camera_id,
                stream_url=settings.video_rtsp_url or None,
                file_path=str(demo_path) if demo_path.exists() else None,
                start_time=now,
                status="RECORDING",
            )
        )
        self.db.commit()
        self.db.refresh(record)
        return VideoRecordOut.model_validate(record)

    def stop_recording(self, experiment_id: int) -> VideoRecordOut:
        self._ensure_experiment(experiment_id)
        active = self.repo.get_active(experiment_id)
        if not active:
            raise HTTPException(status_code=400, detail="当前无进行中的视频录制")
        now = datetime.now()
        active.status = "STOPPED"
        active.end_time = now
        self.db.commit()
        self.db.refresh(active)
        return VideoRecordOut.model_validate(active)

    def list_records(
        self, experiment_id: int, page: int = 1, page_size: int = 20
    ) -> PageResult[VideoRecordOut]:
        self._ensure_experiment(experiment_id)
        items, total = self.repo.list_by_experiment(experiment_id, page, page_size)
        return PageResult[VideoRecordOut](
            items=[VideoRecordOut.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def resolve_demo_file(self, experiment_id: int) -> Path:
        self._ensure_experiment(experiment_id)
        path = self._demo_file_path()
        if not path.exists():
            raise HTTPException(
                status_code=404,
                detail="演示视频未就绪，请将 demo_pool.mp4 放入 uploads/videos/",
            )
        return path

    def generate_synthetic_frame(self, frame_index: int) -> bytes:
        """生成 MJPEG 占位帧。"""
        try:
            import cv2
            import numpy as np
        except ImportError:
            return self._fallback_jpeg_frame(frame_index)

        w, h = 640, 360
        img = np.full((h, w, 3), (12, 74, 110), dtype=np.uint8)
        t = frame_index * 0.05
        cx = int(w * (0.3 + 0.4 * (0.5 + 0.5 * math.sin(t))))
        cy = int(h * (0.5 + 0.2 * math.cos(t * 0.7)))
        cv2.rectangle(img, (0, h - 40), (w, h), (20, 100, 140), -1)
        cv2.putText(
            img,
            "LakeSea Demo Pool",
            (16, h - 14),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (200, 230, 255),
            1,
        )
        cv2.rectangle(img, (cx - 30, cy - 15), (cx + 30, cy + 15), (0, 200, 255), -1)
        cv2.rectangle(img, (cx - 32, cy - 17), (cx + 32, cy + 17), (255, 220, 0), 2)
        _, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        return buf.tobytes()

    @staticmethod
    def _fallback_jpeg_frame(frame_index: int) -> bytes:
        try:
            from PIL import Image, ImageDraw

            w, h = 640, 360
            img = Image.new("RGB", (w, h), (12, 74, 110))
            draw = ImageDraw.Draw(img)
            t = frame_index * 0.05
            cx = int(w * (0.3 + 0.4 * (0.5 + 0.5 * math.sin(t))))
            cy = int(h * (0.5 + 0.2 * math.cos(t * 0.7)))
            draw.rectangle([0, h - 40, w, h], fill=(20, 100, 140))
            draw.text((16, h - 28), "LakeSea Demo Pool", fill=(200, 230, 255))
            draw.rectangle([cx - 30, cy - 15, cx + 30, cy + 15], fill=(0, 200, 255), outline=(255, 220, 0), width=2)
            import io

            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=80)
            return buf.getvalue()
        except ImportError:
            return b""
