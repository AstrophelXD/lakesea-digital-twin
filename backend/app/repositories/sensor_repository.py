from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.monitor import SensorData, ShipTrack


class SensorRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_sensor_row(self, row: SensorData) -> None:
        self.db.add(row)

    def add_track_row(self, row: ShipTrack) -> None:
        self.db.add(row)

    def list_recent_sensor(
        self, experiment_id: int, limit: int = 100
    ) -> List[SensorData]:
        stmt = (
            select(SensorData)
            .where(SensorData.experiment_id == experiment_id)
            .order_by(SensorData.timestamp.desc())
            .limit(limit)
        )
        return list(reversed(self.db.scalars(stmt).all()))

    def list_tracks(
        self, experiment_id: int, limit: int = 500
    ) -> List[ShipTrack]:
        stmt = (
            select(ShipTrack)
            .where(ShipTrack.experiment_id == experiment_id)
            .order_by(ShipTrack.timestamp.asc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def count_sensor(self, experiment_id: int) -> int:
        return (
            self.db.scalar(
                select(func.count())
                .select_from(SensorData)
                .where(SensorData.experiment_id == experiment_id)
            )
            or 0
        )
