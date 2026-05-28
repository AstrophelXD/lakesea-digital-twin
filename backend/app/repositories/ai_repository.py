from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.archive import AiReport


class AiReportRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, report_id: int) -> Optional[AiReport]:
        return self.db.scalar(
            select(AiReport).where(
                AiReport.id == report_id,
                AiReport.is_deleted == 0,
            )
        )

    def get_by_experiment(self, experiment_id: int) -> Optional[AiReport]:
        return self.db.scalar(
            select(AiReport)
            .where(
                AiReport.experiment_id == experiment_id,
                AiReport.is_deleted == 0,
            )
            .order_by(AiReport.generated_time.desc())
        )

    def list_by_experiment(self, experiment_id: int) -> List[AiReport]:
        stmt = (
            select(AiReport)
            .where(
                AiReport.experiment_id == experiment_id,
                AiReport.is_deleted == 0,
            )
            .order_by(AiReport.generated_time.desc())
        )
        return list(self.db.scalars(stmt).all())

    def create(self, report: AiReport) -> AiReport:
        self.db.add(report)
        self.db.flush()
        return report

    def soft_delete(self, report: AiReport) -> None:
        report.is_deleted = 1
