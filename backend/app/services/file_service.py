import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.archive import ExperimentFile
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.file_repository import FileRepository
from app.schemas.archive_schema import ExperimentFileOut


class FileService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = FileRepository(db)
        self.experiment_repo = ExperimentRepository(db)
        self.settings = get_settings()

    def _ensure_upload_dir(self, experiment_id: int) -> Path:
        base = Path(self.settings.upload_dir) / str(experiment_id)
        base.mkdir(parents=True, exist_ok=True)
        return base

    def list_files(self, experiment_id: int) -> list[ExperimentFileOut]:
        return [
            ExperimentFileOut.model_validate(f)
            for f in self.repo.list_by_experiment(experiment_id)
        ]

    async def upload(
        self,
        experiment_id: int,
        file: UploadFile,
        file_type: str | None,
        uploader_id: int,
    ) -> ExperimentFileOut:
        task = self.experiment_repo.get_by_id(experiment_id)
        if not task:
            raise HTTPException(status_code=404, detail="试验任务不存在")

        original = file.filename or "upload.bin"
        ext = Path(original).suffix
        stored_name = f"{uuid.uuid4().hex}{ext}"
        dest_dir = self._ensure_upload_dir(experiment_id)
        dest_path = dest_dir / stored_name

        content = await file.read()
        dest_path.write_bytes(content)

        row = ExperimentFile(
            experiment_id=experiment_id,
            file_name=original,
            file_type=file_type or "OTHER",
            file_path=str(dest_path).replace("\\", "/"),
            upload_by=uploader_id,
            is_deleted=0,
        )
        self.repo.create(row)
        self.db.commit()
        self.db.refresh(row)
        return ExperimentFileOut.model_validate(row)

    def get_file_path(self, file_id: int) -> tuple[ExperimentFile, str]:
        row = self.repo.get_by_id(file_id)
        if not row:
            raise HTTPException(status_code=404, detail="文件不存在")
        if not os.path.isfile(row.file_path):
            raise HTTPException(status_code=404, detail="文件已丢失")
        return row, row.file_path
