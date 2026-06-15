"""试验/预约生命周期与资源占用状态（AVAILABLE / RESERVED / IN_USE）同步。"""

from __future__ import annotations

from typing import Iterable, Optional, Set

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.constants import (
    APPROVED,
    AVAILABLE,
    IN_USE,
    PENDING_DIRECTOR,
    PENDING_TEACHER,
    RESERVED,
    RESOURCE_UNAVAILABLE,
    RUNNING,
)
from app.models.experiment import ExperimentTask
from app.models.reservation import ExpReservation, ExpReservationResource
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.resource_repository import ResourceRepository
from app.repositories.reservation_repository import ReservationRepository


class ResourceOccupancyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.resource_repo = ResourceRepository(db)
        self.reservation_repo = ReservationRepository(db)
        self.experiment_repo = ExperimentRepository(db)

    def _resource_ids_for_reservation(self, reservation_id: int) -> Set[int]:
        reservation = self.reservation_repo.get_detail(reservation_id)
        if not reservation:
            return set()
        return {rr.resource_id for rr in reservation.resources}

    def _can_auto_manage(self, status: str) -> bool:
        return status not in RESOURCE_UNAVAILABLE

    def _is_resource_still_needed(
        self,
        resource_id: int,
        *,
        exclude_reservation_id: Optional[int] = None,
        exclude_task_id: Optional[int] = None,
    ) -> bool:
        running_stmt = (
            select(ExperimentTask.id)
            .join(ExpReservation, ExperimentTask.reservation_id == ExpReservation.id)
            .join(
                ExpReservationResource,
                ExpReservationResource.reservation_id == ExpReservation.id,
            )
            .where(
                ExperimentTask.is_deleted == 0,
                ExperimentTask.status == RUNNING,
                ExpReservationResource.resource_id == resource_id,
            )
            .limit(1)
        )
        if exclude_task_id:
            running_stmt = running_stmt.where(ExperimentTask.id != exclude_task_id)
        if self.db.scalar(running_stmt):
            return True

        active_reservation_statuses = (
            PENDING_TEACHER,
            PENDING_DIRECTOR,
            APPROVED,
        )
        reserved_stmt = (
            select(ExpReservation.id)
            .join(
                ExpReservationResource,
                ExpReservationResource.reservation_id == ExpReservation.id,
            )
            .where(
                ExpReservation.is_deleted == 0,
                ExpReservation.status.in_(active_reservation_statuses),
                ExpReservationResource.resource_id == resource_id,
            )
            .limit(1)
        )
        if exclude_reservation_id:
            reserved_stmt = reserved_stmt.where(ExpReservation.id != exclude_reservation_id)
        return self.db.scalar(reserved_stmt) is not None

    def _set_status_for_resources(
        self,
        resource_ids: Iterable[int],
        status: str,
        *,
        allowed_from: Optional[Set[str]] = None,
    ) -> None:
        for resource_id in resource_ids:
            resource = self.resource_repo.get_by_id(resource_id)
            if not resource or not self._can_auto_manage(resource.status):
                continue
            if allowed_from is not None and resource.status not in allowed_from:
                continue
            resource.status = status

    def reserve_for_reservation(self, reservation_id: int) -> None:
        """主任审批通过后：资源标记为已预约。"""
        self._set_status_for_resources(
            self._resource_ids_for_reservation(reservation_id),
            RESERVED,
            allowed_from={AVAILABLE, RESERVED},
        )

    def mark_in_use_for_task(self, task_id: int) -> None:
        """试验启动：关联资源标记为使用中。"""
        task = self.experiment_repo.get_by_id(task_id)
        if not task:
            return
        self._set_status_for_resources(
            self._resource_ids_for_reservation(task.reservation_id),
            IN_USE,
            allowed_from={AVAILABLE, RESERVED, IN_USE},
        )

    def release_for_task(self, task_id: int) -> None:
        """试验完成/归档：若无其他占用则释放资源。"""
        task = self.experiment_repo.get_by_id(task_id)
        if not task:
            return
        reservation_id = task.reservation_id
        for resource_id in self._resource_ids_for_reservation(reservation_id):
            if self._is_resource_still_needed(
                resource_id,
                exclude_reservation_id=reservation_id,
                exclude_task_id=task_id,
            ):
                continue
            resource = self.resource_repo.get_by_id(resource_id)
            if resource and self._can_auto_manage(resource.status):
                resource.status = AVAILABLE

    def release_for_reservation(self, reservation_id: int) -> None:
        """预约取消/驳回后：释放尚未被其他预约或试验占用的资源。"""
        for resource_id in self._resource_ids_for_reservation(reservation_id):
            if self._is_resource_still_needed(
                resource_id,
                exclude_reservation_id=reservation_id,
            ):
                continue
            resource = self.resource_repo.get_by_id(resource_id)
            if resource and self._can_auto_manage(resource.status):
                resource.status = AVAILABLE

    def reconcile_running_tasks(self) -> None:
        """启动时修复：将执行中试验关联资源同步为 IN_USE。"""
        task_ids = list(
            self.db.scalars(
                select(ExperimentTask.id).where(
                    ExperimentTask.is_deleted == 0,
                    ExperimentTask.status == RUNNING,
                )
            ).all()
        )
        for task_id in task_ids:
            self.mark_in_use_for_task(task_id)
