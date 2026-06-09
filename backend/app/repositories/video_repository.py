import json
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.video_record import VideoRecord


class VideoRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, record_id: int) -> Optional[VideoRecord]:
        return self.db.get(VideoRecord, record_id)

    def create(self, record: VideoRecord) -> VideoRecord:
        self.db.add(record)
        self.db.flush()
        return record

    def update(self, record: VideoRecord) -> VideoRecord:
        self.db.flush()
        return record

    def get_active(self, experiment_id: int) -> Optional[VideoRecord]:
        stmt = (
            select(VideoRecord)
            .where(
                VideoRecord.experiment_id == experiment_id,
                VideoRecord.status == "RECORDING",
            )
            .order_by(VideoRecord.start_time.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def list_by_experiment(
        self, experiment_id: int, page: int = 1, page_size: int = 20
    ) -> Tuple[List[VideoRecord], int]:
        stmt = select(VideoRecord).where(VideoRecord.experiment_id == experiment_id)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(
            self.db.scalars(
                stmt.order_by(VideoRecord.create_time.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return items, total

    def stop_active(self, experiment_id: int, end_time: datetime) -> None:
        active = self.get_active(experiment_id)
        if active:
            active.status = "STOPPED"
            active.end_time = end_time
