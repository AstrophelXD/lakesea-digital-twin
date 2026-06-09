from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.archive import AiCallLog


class AiLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, log: AiCallLog) -> AiCallLog:
        self.db.add(log)
        self.db.flush()
        return log

    def list_logs(
        self,
        experiment_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[AiCallLog], int]:
        stmt = select(AiCallLog).order_by(AiCallLog.call_time.desc())
        if experiment_id is not None:
            stmt = stmt.where(AiCallLog.experiment_id == experiment_id)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(
            self.db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
        )
        return items, total
