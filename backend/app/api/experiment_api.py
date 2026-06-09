from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.core.deps import CurrentUser, DbSession
from app.core.response import success
from app.services.archive_export_service import ArchiveExportService
from app.services.experiment_service import ExperimentService

router = APIRouter(prefix="/api/experiments", tags=["试验任务"])


@router.get("")
def list_experiments(
    db: DbSession,
    _: CurrentUser,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
):
    result = ExperimentService(db).list_tasks(status, page, page_size)
    return success(result.model_dump(by_alias=True))


@router.get("/{task_id}")
def get_experiment(task_id: int, db: DbSession, _: CurrentUser):
    result = ExperimentService(db).get_task(task_id)
    return success(result.model_dump(by_alias=True))


@router.post("/{task_id}/ready")
def mark_ready(task_id: int, db: DbSession, current_user: CurrentUser):
    result = ExperimentService(db).mark_ready(task_id, current_user)
    return success(result.model_dump(by_alias=True))


@router.post("/{task_id}/start")
def start_experiment(task_id: int, db: DbSession, current_user: CurrentUser):
    result = ExperimentService(db).start(task_id, current_user)
    return success(result.model_dump(by_alias=True))


@router.post("/{task_id}/finish")
def finish_experiment(task_id: int, db: DbSession, current_user: CurrentUser):
    result = ExperimentService(db).finish(task_id, current_user)
    return success(result.model_dump(by_alias=True))


@router.post("/{task_id}/archive")
def archive_experiment(task_id: int, db: DbSession, current_user: CurrentUser):
    result = ExperimentService(db).archive(task_id, current_user)
    return success(result.model_dump(by_alias=True))


@router.get("/{task_id}/replay")
def experiment_replay(task_id: int, db: DbSession, _: CurrentUser):
    result = ExperimentService(db).get_replay(task_id)
    return success(result.model_dump(by_alias=True))


@router.get("/{task_id}/export/sensor-csv")
def export_sensor_csv(task_id: int, db: DbSession, _: CurrentUser):
    filename, content = ArchiveExportService(db).export_sensor_csv(task_id)
    return Response(
        content=content.encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{task_id}/export/track-json")
def export_track_json(task_id: int, db: DbSession, _: CurrentUser):
    filename, content = ArchiveExportService(db).export_track_json(task_id)
    return Response(
        content=content.encode("utf-8"),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{task_id}/export/ai-report")
def export_ai_report(
    task_id: int,
    db: DbSession,
    _: CurrentUser,
    fmt: str = Query("markdown", pattern="^(markdown|html)$"),
):
    media_type, filename, content = ArchiveExportService(db).export_ai_report(task_id, fmt)
    return Response(
        content=content.encode("utf-8"),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
