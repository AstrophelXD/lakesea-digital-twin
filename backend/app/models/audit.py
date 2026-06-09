from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SysOperationLog(Base):
    __tablename__ = "SYS_OPERATION_LOG"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column("USER_ID", Integer)
    username: Mapped[Optional[str]] = mapped_column("USERNAME", String(50))
    module: Mapped[str] = mapped_column("MODULE", String(50), nullable=False)
    action: Mapped[str] = mapped_column("ACTION", String(50), nullable=False)
    target_type: Mapped[Optional[str]] = mapped_column("TARGET_TYPE", String(50))
    target_id: Mapped[Optional[int]] = mapped_column("TARGET_ID", Integer)
    detail: Mapped[Optional[str]] = mapped_column("DETAIL", Text)
    ip_address: Mapped[Optional[str]] = mapped_column("IP_ADDRESS", String(50))
    success: Mapped[int] = mapped_column("SUCCESS", Integer, default=1)
    create_time: Mapped[datetime] = mapped_column(
        "CREATE_TIME", DateTime, server_default=func.now()
    )
