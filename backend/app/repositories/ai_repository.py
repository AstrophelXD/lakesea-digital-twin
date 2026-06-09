from typing import List, Optional, Tuple

from sqlalchemy import func, select
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

    def list_reports(
        self, page: int = 1, page_size: int = 20
    ) -> Tuple[List[AiReport], int]:
        stmt = (
            select(AiReport)
            .where(AiReport.is_deleted == 0)
            .order_by(AiReport.generated_time.desc())
        )
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(
            self.db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
        )
        return items, total
