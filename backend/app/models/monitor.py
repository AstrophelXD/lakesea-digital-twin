from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SensorData(Base):
    __tablename__ = "SENSOR_DATA"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column("EXPERIMENT_ID", Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column("TIMESTAMP", DateTime, nullable=False)
    position_x: Mapped[Optional[Decimal]] = mapped_column("POSITION_X", Numeric(10, 2))
    position_y: Mapped[Optional[Decimal]] = mapped_column("POSITION_Y", Numeric(10, 2))
    speed: Mapped[Optional[Decimal]] = mapped_column("SPEED", Numeric(10, 2))
    heading: Mapped[Optional[Decimal]] = mapped_column("HEADING", Numeric(10, 2))
    roll: Mapped[Optional[Decimal]] = mapped_column("ROLL", Numeric(10, 2))
    pitch: Mapped[Optional[Decimal]] = mapped_column("PITCH", Numeric(10, 2))
    battery: Mapped[Optional[Decimal]] = mapped_column("BATTERY", Numeric(10, 2))
    resistance: Mapped[Optional[Decimal]] = mapped_column("RESISTANCE", Numeric(10, 2))


class ShipTrack(Base):
    __tablename__ = "SHIP_TRACK"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column("EXPERIMENT_ID", Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column("TIMESTAMP", DateTime, nullable=False)
    position_x: Mapped[Optional[Decimal]] = mapped_column("POSITION_X", Numeric(10, 2))
    position_y: Mapped[Optional[Decimal]] = mapped_column("POSITION_Y", Numeric(10, 2))
    heading: Mapped[Optional[Decimal]] = mapped_column("HEADING", Numeric(10, 2))


class AlarmRecord(Base):
    __tablename__ = "ALARM_RECORD"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column("EXPERIMENT_ID", Integer, nullable=False)
    alarm_type: Mapped[str] = mapped_column("ALARM_TYPE", String(50), nullable=False)
    alarm_level: Mapped[Optional[str]] = mapped_column("ALARM_LEVEL", String(20))
    alarm_message: Mapped[Optional[str]] = mapped_column("ALARM_MESSAGE", String(500))
    handle_status: Mapped[str] = mapped_column("HANDLE_STATUS", String(20), default="PENDING")
    handler_id: Mapped[Optional[int]] = mapped_column("HANDLER_ID", Integer)
    handle_time: Mapped[Optional[datetime]] = mapped_column("HANDLE_TIME", DateTime)
    handle_comment: Mapped[Optional[str]] = mapped_column("HANDLE_COMMENT", String(500))
    create_time: Mapped[datetime] = mapped_column(
        "CREATE_TIME", DateTime, server_default=func.now()
    )
