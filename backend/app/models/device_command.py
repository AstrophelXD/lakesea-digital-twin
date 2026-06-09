from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DeviceCommandLog(Base):
    __tablename__ = "DEVICE_COMMAND_LOG"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column("DEVICE_ID", String(50), nullable=False)
    experiment_id: Mapped[Optional[int]] = mapped_column("EXPERIMENT_ID", Integer)
    command_type: Mapped[str] = mapped_column("COMMAND_TYPE", String(50), nullable=False)
    command_payload: Mapped[Optional[str]] = mapped_column("COMMAND_PAYLOAD", Text)
    issued_by: Mapped[Optional[int]] = mapped_column("ISSUED_BY", Integer)
    issued_at: Mapped[datetime] = mapped_column(
        "ISSUED_AT", DateTime, server_default=func.now()
    )
    status: Mapped[str] = mapped_column("STATUS", String(20), default="PENDING")
    result_message: Mapped[Optional[str]] = mapped_column("RESULT_MESSAGE", String(500))
