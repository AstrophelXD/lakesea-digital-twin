from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.experiment import ExperimentTask


class ExperimentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, task_id: int) -> Optional[ExperimentTask]:
        return self.db.scalar(
            select(ExperimentTask).where(
                ExperimentTask.id == task_id,
                ExperimentTask.is_deleted == 0,
            )
        )

    def get_by_reservation_id(self, reservation_id: int) -> Optional[ExperimentTask]:
        return self.db.scalar(
            select(ExperimentTask).where(
                ExperimentTask.reservation_id == reservation_id,
                ExperimentTask.is_deleted == 0,
            )
        )

    def list_tasks(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ExperimentTask], int]:
        stmt = select(ExperimentTask).where(ExperimentTask.is_deleted == 0)
        if status:
            stmt = stmt.where(ExperimentTask.status == status)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(
            self.db.scalars(
                stmt.order_by(ExperimentTask.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return items, total

    def create(self, task: ExperimentTask) -> ExperimentTask:
        self.db.add(task)
        self.db.flush()
        return task
