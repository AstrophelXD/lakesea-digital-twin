from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ExpReservation(Base):
    __tablename__ = "EXP_RESERVATION"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True, autoincrement=True)
    reservation_no: Mapped[str] = mapped_column("RESERVATION_NO", String(50), unique=True, nullable=False)
    exp_name: Mapped[str] = mapped_column("EXP_NAME", String(100), nullable=False)
    exp_type: Mapped[Optional[str]] = mapped_column("EXP_TYPE", String(50))
    applicant_id: Mapped[int] = mapped_column("APPLICANT_ID", Integer, nullable=False)
    teacher_id: Mapped[Optional[int]] = mapped_column("TEACHER_ID", Integer)
    start_time: Mapped[datetime] = mapped_column("START_TIME", DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column("END_TIME", DateTime, nullable=False)
    status: Mapped[str] = mapped_column("STATUS", String(30), default="DRAFT")
    purpose: Mapped[Optional[str]] = mapped_column("PURPOSE", Text)
    plan_summary: Mapped[Optional[str]] = mapped_column("PLAN_SUMMARY", Text)
    submit_time: Mapped[Optional[datetime]] = mapped_column("SUBMIT_TIME", DateTime)
    teacher_review_by: Mapped[Optional[int]] = mapped_column("TEACHER_REVIEW_BY", Integer)
    teacher_review_time: Mapped[Optional[datetime]] = mapped_column("TEACHER_REVIEW_TIME", DateTime)
    teacher_review_comment: Mapped[Optional[str]] = mapped_column("TEACHER_REVIEW_COMMENT", String(500))
    director_approved_by: Mapped[Optional[int]] = mapped_column("DIRECTOR_APPROVED_BY", Integer)
    director_approved_time: Mapped[Optional[datetime]] = mapped_column("DIRECTOR_APPROVED_TIME", DateTime)
    director_approval_comment: Mapped[Optional[str]] = mapped_column("DIRECTOR_APPROVAL_COMMENT", String(500))
    reject_reason: Mapped[Optional[str]] = mapped_column("REJECT_REASON", String(500))
    create_time: Mapped[datetime] = mapped_column(
        "CREATE_TIME", DateTime, server_default=func.now()
    )
    update_time: Mapped[datetime] = mapped_column(
        "UPDATE_TIME", DateTime, server_default=func.now(), onupdate=func.now()
    )
    is_deleted: Mapped[int] = mapped_column("IS_DELETED", Integer, default=0)

    resources: Mapped[List["ExpReservationResource"]] = relationship(
        back_populates="reservation", cascade="all, delete-orphan"
    )
    approval_logs: Mapped[List["ExpApprovalLog"]] = relationship(
        back_populates="reservation", cascade="all, delete-orphan"
    )


class ExpReservationResource(Base):
    __tablename__ = "EXP_RESERVATION_RESOURCE"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True, autoincrement=True)
    reservation_id: Mapped[int] = mapped_column(
        "RESERVATION_ID", Integer, ForeignKey("EXP_RESERVATION.ID"), nullable=False
    )
    resource_id: Mapped[int] = mapped_column("RESOURCE_ID", Integer, nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column("RESOURCE_TYPE", String(50))
    quantity: Mapped[int] = mapped_column("QUANTITY", Integer, default=1)
    start_time: Mapped[datetime] = mapped_column("START_TIME", DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column("END_TIME", DateTime, nullable=False)
    remark: Mapped[Optional[str]] = mapped_column("REMARK", String(500))

    reservation: Mapped["ExpReservation"] = relationship(back_populates="resources")


class ExpApprovalLog(Base):
    __tablename__ = "EXP_APPROVAL_LOG"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True, autoincrement=True)
    reservation_id: Mapped[int] = mapped_column(
        "RESERVATION_ID", Integer, ForeignKey("EXP_RESERVATION.ID"), nullable=False
    )
    step_type: Mapped[str] = mapped_column("STEP_TYPE", String(30), nullable=False)
    approver_id: Mapped[int] = mapped_column("APPROVER_ID", Integer, nullable=False)
    result: Mapped[str] = mapped_column("RESULT", String(20), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column("COMMENT", String(500))
    action_time: Mapped[datetime] = mapped_column(
        "ACTION_TIME", DateTime, server_default=func.now()
    )

    reservation: Mapped["ExpReservation"] = relationship(back_populates="approval_logs")
