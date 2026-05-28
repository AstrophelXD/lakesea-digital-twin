from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.monitor import AlarmRecord


class AlarmRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, alarm_id: int) -> Optional[AlarmRecord]:
        return self.db.get(AlarmRecord, alarm_id)

    def create(self, alarm: AlarmRecord) -> AlarmRecord:
        self.db.add(alarm)
        self.db.flush()
        return alarm

    def list_alarms(
        self,
        experiment_id: Optional[int] = None,
        handle_status: Optional[str] = None,
        alarm_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[AlarmRecord], int]:
        stmt = select(AlarmRecord)
        if experiment_id is not None:
            stmt = stmt.where(AlarmRecord.experiment_id == experiment_id)
        if handle_status:
            stmt = stmt.where(AlarmRecord.handle_status == handle_status)
        if alarm_type:
            stmt = stmt.where(AlarmRecord.alarm_type == alarm_type)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(
            self.db.scalars(
                stmt.order_by(AlarmRecord.create_time.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return items, total

    def has_recent_alarm(
        self,
        experiment_id: int,
        alarm_type: str,
        since: datetime,
    ) -> bool:
        stmt = select(AlarmRecord).where(
            AlarmRecord.experiment_id == experiment_id,
            AlarmRecord.alarm_type == alarm_type,
            AlarmRecord.create_time >= since,
        )
        return self.db.scalar(stmt) is not None
