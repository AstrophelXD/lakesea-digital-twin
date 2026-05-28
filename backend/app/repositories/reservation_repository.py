from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.constants import RESERVATION_ACTIVE_STATUSES
from app.models.reservation import ExpApprovalLog, ExpReservation, ExpReservationResource


class ReservationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, reservation_id: int) -> Optional[ExpReservation]:
        return self.db.scalar(
            select(ExpReservation).where(
                ExpReservation.id == reservation_id,
                ExpReservation.is_deleted == 0,
            )
        )

    def get_detail(self, reservation_id: int) -> Optional[ExpReservation]:
        return self.db.scalar(
            select(ExpReservation)
            .options(
                joinedload(ExpReservation.resources),
                joinedload(ExpReservation.approval_logs),
            )
            .where(
                ExpReservation.id == reservation_id,
                ExpReservation.is_deleted == 0,
            )
        )

    def list_reservations(
        self,
        status: Optional[str] = None,
        applicant_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ExpReservation], int]:
        stmt = select(ExpReservation).where(ExpReservation.is_deleted == 0)
        if status:
            stmt = stmt.where(ExpReservation.status == status)
        if applicant_id is not None:
            stmt = stmt.where(ExpReservation.applicant_id == applicant_id)
        if teacher_id is not None:
            stmt = stmt.where(ExpReservation.teacher_id == teacher_id)
        if keyword:
            stmt = stmt.where(ExpReservation.exp_name.like(f"%{keyword}%"))
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(
            self.db.scalars(
                stmt.order_by(ExpReservation.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return items, total

    def find_conflicts(
        self,
        resource_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_reservation_id: Optional[int] = None,
    ) -> List[ExpReservation]:
        stmt = (
            select(ExpReservation)
            .join(
                ExpReservationResource,
                ExpReservationResource.reservation_id == ExpReservation.id,
            )
            .where(
                ExpReservation.is_deleted == 0,
                ExpReservation.status.in_(RESERVATION_ACTIVE_STATUSES),
                ExpReservationResource.resource_id == resource_id,
                ExpReservationResource.start_time < end_time,
                ExpReservationResource.end_time > start_time,
            )
        )
        if exclude_reservation_id:
            stmt = stmt.where(ExpReservation.id != exclude_reservation_id)
        return list(self.db.scalars(stmt).unique().all())

    def create(self, reservation: ExpReservation) -> ExpReservation:
        self.db.add(reservation)
        self.db.flush()
        return reservation

    def add_approval_log(self, log: ExpApprovalLog) -> None:
        self.db.add(log)

    def delete_resources_by_reservation(self, reservation_id: int) -> None:
        for row in self.db.scalars(
            select(ExpReservationResource).where(
                ExpReservationResource.reservation_id == reservation_id
            )
        ).all():
            self.db.delete(row)
