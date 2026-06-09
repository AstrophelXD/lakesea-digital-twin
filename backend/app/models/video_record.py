from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VideoRecord(Base):
    __tablename__ = "VIDEO_RECORD"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column("EXPERIMENT_ID", Integer, nullable=False)
    camera_id: Mapped[str] = mapped_column("CAMERA_ID", String(50), nullable=False)
    stream_url: Mapped[Optional[str]] = mapped_column("STREAM_URL", String(500))
    file_path: Mapped[Optional[str]] = mapped_column("FILE_PATH", String(500))
    start_time: Mapped[Optional[datetime]] = mapped_column("START_TIME", DateTime)
    end_time: Mapped[Optional[datetime]] = mapped_column("END_TIME", DateTime)
    status: Mapped[str] = mapped_column("STATUS", String(20), default="IDLE")
    create_time: Mapped[datetime] = mapped_column(
        "CREATE_TIME", DateTime, server_default=func.now()
    )
