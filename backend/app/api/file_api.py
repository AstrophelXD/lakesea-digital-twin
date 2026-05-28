from typing import Optional

from fastapi import APIRouter, File, Form, Query, UploadFile
from fastapi.responses import FileResponse

from app.core.deps import CurrentUser, DbSession
from app.core.response import success
from app.services.file_service import FileService

router = APIRouter(prefix="/api/files", tags=["试验文件"])


@router.get("")
def list_files(
    db: DbSession,
    _: CurrentUser,
    experiment_id: int = Query(..., alias="experimentId"),
):
    items = FileService(db).list_files(experiment_id)
    return success([i.model_dump(by_alias=True) for i in items])


@router.post("/upload")
async def upload_file(
    db: DbSession,
    current_user: CurrentUser,
    experiment_id: int = Form(..., alias="experimentId"),
    file_type: Optional[str] = Form(None, alias="fileType"),
    file: UploadFile = File(...),
):
    result = await FileService(db).upload(
        experiment_id, file, file_type, current_user.id
    )
    return success(result.model_dump(by_alias=True))


@router.get("/{file_id}/download")
def download_file(file_id: int, db: DbSession, _: CurrentUser):
    row, path = FileService(db).get_file_path(file_id)
    return FileResponse(
        path,
        filename=row.file_name,
        media_type="application/octet-stream",
    )
