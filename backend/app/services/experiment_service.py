from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.constants import PENDING_PREPARE, READY, RUNNING, TASK_COMPLETED, TASK_ARCHIVED
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.reservation_repository import ReservationRepository
from app.schemas.common import PageResult
from app.schemas.experiment_schema import ExperimentOut


class ExperimentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ExperimentRepository(db)
        self.reservation_repo = ReservationRepository(db)

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

    def mark_ready(self, task_id: int) -> ExperimentOut:
        task = self._get_task_or_404(task_id)
        if task.status != PENDING_PREPARE:
            raise HTTPException(status_code=400, detail="仅待准备状态可标记为已准备")
        task.status = READY
        self.db.commit()
        self.db.refresh(task)
        return ExperimentOut.model_validate(task)

    def start(self, task_id: int) -> ExperimentOut:
        from datetime import datetime

        task = self._get_task_or_404(task_id)
        if task.status != READY:
            raise HTTPException(status_code=400, detail="仅已准备状态可启动试验")
        task.status = RUNNING
        task.actual_start_time = datetime.now()
        self.db.commit()
        self.db.refresh(task)
        return ExperimentOut.model_validate(task)

    def finish(self, task_id: int) -> ExperimentOut:
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
        return ExperimentOut.model_validate(task)

    def archive(self, task_id: int) -> ExperimentOut:
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
        return ExperimentOut.model_validate(task)
