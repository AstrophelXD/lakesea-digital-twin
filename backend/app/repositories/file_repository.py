from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.archive import ExperimentFile


class FileRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, file_id: int) -> Optional[ExperimentFile]:
        return self.db.scalar(
            select(ExperimentFile).where(
                ExperimentFile.id == file_id,
                ExperimentFile.is_deleted == 0,
            )
        )

    def list_by_experiment(self, experiment_id: int) -> List[ExperimentFile]:
        stmt = (
            select(ExperimentFile)
            .where(
                ExperimentFile.experiment_id == experiment_id,
                ExperimentFile.is_deleted == 0,
            )
            .order_by(ExperimentFile.upload_time.desc())
        )
        return list(self.db.scalars(stmt).all())

    def create(self, row: ExperimentFile) -> ExperimentFile:
        self.db.add(row)
        self.db.flush()
        return row
