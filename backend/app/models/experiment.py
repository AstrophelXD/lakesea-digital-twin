from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ExperimentTask(Base):
    __tablename__ = "EXPERIMENT_TASK"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True, autoincrement=True)
    task_no: Mapped[str] = mapped_column("TASK_NO", String(50), unique=True, nullable=False)
    reservation_id: Mapped[int] = mapped_column("RESERVATION_ID", Integer, nullable=False)
    exp_name: Mapped[str] = mapped_column("EXP_NAME", String(100), nullable=False)
    status: Mapped[str] = mapped_column("STATUS", String(30), default="PENDING_PREPARE")
    actual_start_time: Mapped[Optional[datetime]] = mapped_column("ACTUAL_START_TIME", DateTime)
    actual_end_time: Mapped[Optional[datetime]] = mapped_column("ACTUAL_END_TIME", DateTime)
    operator_id: Mapped[Optional[int]] = mapped_column("OPERATOR_ID", Integer)
    archive_time: Mapped[Optional[datetime]] = mapped_column("ARCHIVE_TIME", DateTime)
    create_time: Mapped[datetime] = mapped_column(
        "CREATE_TIME", DateTime, server_default=func.now()
    )
    update_time: Mapped[datetime] = mapped_column(
        "UPDATE_TIME", DateTime, server_default=func.now(), onupdate=func.now()
    )
    is_deleted: Mapped[int] = mapped_column("IS_DELETED", Integer, default=0)
