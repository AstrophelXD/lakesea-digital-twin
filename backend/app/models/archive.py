from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ExperimentFile(Base):
    __tablename__ = "EXPERIMENT_FILE"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column("EXPERIMENT_ID", Integer, nullable=False)
    file_name: Mapped[str] = mapped_column("FILE_NAME", String(200), nullable=False)
    file_type: Mapped[Optional[str]] = mapped_column("FILE_TYPE", String(50))
    file_path: Mapped[str] = mapped_column("FILE_PATH", String(500), nullable=False)
    upload_by: Mapped[Optional[int]] = mapped_column("UPLOAD_BY", Integer)
    upload_time: Mapped[datetime] = mapped_column(
        "UPLOAD_TIME", DateTime, server_default=func.now()
    )
    is_deleted: Mapped[int] = mapped_column("IS_DELETED", Integer, default=0)


class AiReport(Base):
    __tablename__ = "AI_REPORT"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column("EXPERIMENT_ID", Integer, nullable=False)
    report_title: Mapped[Optional[str]] = mapped_column("REPORT_TITLE", String(200))
    analysis_type: Mapped[Optional[str]] = mapped_column("ANALYSIS_TYPE", String(50))
    summary_text: Mapped[Optional[str]] = mapped_column("SUMMARY_TEXT", Text)
    analysis_text: Mapped[Optional[str]] = mapped_column("ANALYSIS_TEXT", Text)
    model_name: Mapped[Optional[str]] = mapped_column("MODEL_NAME", String(100))
    generated_by: Mapped[Optional[int]] = mapped_column("GENERATED_BY", Integer)
    generated_time: Mapped[datetime] = mapped_column(
        "GENERATED_TIME", DateTime, server_default=func.now()
    )
    is_deleted: Mapped[int] = mapped_column("IS_DELETED", Integer, default=0)


class AiCallLog(Base):
    __tablename__ = "AI_CALL_LOG"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[Optional[int]] = mapped_column("EXPERIMENT_ID", Integer)
    analysis_type: Mapped[Optional[str]] = mapped_column("ANALYSIS_TYPE", String(50))
    model_name: Mapped[Optional[str]] = mapped_column("MODEL_NAME", String(100))
    is_mock: Mapped[int] = mapped_column("IS_MOCK", Integer, default=0)
    success: Mapped[int] = mapped_column("SUCCESS", Integer, default=1)
    duration_ms: Mapped[Optional[int]] = mapped_column("DURATION_MS", Integer)
    token_used: Mapped[Optional[int]] = mapped_column("TOKEN_USED", Integer)
    error_message: Mapped[Optional[str]] = mapped_column("ERROR_MESSAGE", String(500))
    called_by: Mapped[Optional[int]] = mapped_column("CALLED_BY", Integer)
    call_time: Mapped[datetime] = mapped_column(
        "CALL_TIME", DateTime, server_default=func.now()
    )
