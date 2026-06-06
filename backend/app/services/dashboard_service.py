from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db_info import get_database_type
from app.models.experiment import ExperimentTask
from app.models.monitor import AlarmRecord
from app.models.reservation import ExpReservation
from app.models.resource import LabResource
from app.schemas.dashboard_schema import DashboardSummary, StatusCount, TrendPoint


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_summary(self) -> DashboardSummary:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        today_reservations = self.db.scalar(
            select(func.count())
            .select_from(ExpReservation)
            .where(
                ExpReservation.is_deleted == 0,
                ExpReservation.create_time >= today_start,
                ExpReservation.create_time < today_end,
            )
        ) or 0

        running_experiments = self.db.scalar(
            select(func.count())
            .select_from(ExperimentTask)
            .where(
                ExperimentTask.is_deleted == 0,
                ExperimentTask.status == "RUNNING",
            )
        ) or 0

        available_resources = self.db.scalar(
            select(func.count())
            .select_from(LabResource)
            .where(
                LabResource.is_deleted == 0,
                LabResource.status == "AVAILABLE",
            )
        ) or 0

        pending_alarms = self.db.scalar(
            select(func.count())
            .select_from(AlarmRecord)
            .where(AlarmRecord.handle_status == "PENDING")
        ) or 0

        settings = get_settings()
        return DashboardSummary(
            today_reservations=today_reservations,
            running_experiments=running_experiments,
            available_resources=available_resources,
            pending_alarms=pending_alarms,
            database_type=get_database_type(settings.database_url),
        )

    def reservation_status_distribution(self) -> list[StatusCount]:
        rows = self.db.execute(
            select(ExpReservation.status, func.count())
            .where(ExpReservation.is_deleted == 0)
            .group_by(ExpReservation.status)
        ).all()
        return [StatusCount(status=r[0], count=r[1]) for r in rows]

    def resource_status_distribution(self) -> list[StatusCount]:
        rows = self.db.execute(
            select(LabResource.status, func.count())
            .where(LabResource.is_deleted == 0)
            .group_by(LabResource.status)
        ).all()
        return [StatusCount(status=r[0], count=r[1]) for r in rows]

    def alarm_trend(self, days: int = 7) -> list[TrendPoint]:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start = today - timedelta(days=days - 1)
        timestamps = self.db.scalars(
            select(AlarmRecord.create_time).where(AlarmRecord.create_time >= start)
        ).all()
        count_map: dict[str, int] = {}
        for ts in timestamps:
            key = ts.strftime("%Y-%m-%d")
            count_map[key] = count_map.get(key, 0) + 1
        points: list[TrendPoint] = []
        for i in range(days):
            day = start + timedelta(days=i)
            key = day.strftime("%Y-%m-%d")
            points.append(TrendPoint(date=key, count=count_map.get(key, 0)))
        return points
