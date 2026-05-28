from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LabResource(Base):
    __tablename__ = "LAB_RESOURCE"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True, autoincrement=True)
    resource_code: Mapped[str] = mapped_column("RESOURCE_CODE", String(50), unique=True, nullable=False)
    resource_name: Mapped[str] = mapped_column("RESOURCE_NAME", String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column("RESOURCE_TYPE", String(50), nullable=False)
    status: Mapped[str] = mapped_column("STATUS", String(20), default="AVAILABLE")
    location: Mapped[Optional[str]] = mapped_column("LOCATION", String(200))
    manager_id: Mapped[Optional[int]] = mapped_column("MANAGER_ID", Integer)
    description: Mapped[Optional[str]] = mapped_column("DESCRIPTION", String(500))
    create_time: Mapped[datetime] = mapped_column(
        "CREATE_TIME", DateTime, server_default=func.now()
    )
    update_time: Mapped[datetime] = mapped_column(
        "UPDATE_TIME", DateTime, server_default=func.now(), onupdate=func.now()
    )
    is_deleted: Mapped[int] = mapped_column("IS_DELETED", Integer, default=0)
