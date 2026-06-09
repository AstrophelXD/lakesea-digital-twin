from typing import Optional

from fastapi import APIRouter, Query

from app.core.config import get_settings
from app.core.database import engine
from app.core.db_info import check_db_health
from app.core.deps import CurrentUser, DbSession
from app.core.response import success
from app.services.system_health_service import SystemHealthService

router = APIRouter(prefix="/api/health", tags=["健康检查"])


@router.get("/db")
def db_health():
    settings = get_settings()
    result = check_db_health(engine, settings.database_url)
    return success(result.to_dict())


@router.get("/system")
def system_health(
    db: DbSession,
    _: CurrentUser,
    experiment_id: Optional[int] = Query(None, alias="experimentId"),
):
    result = SystemHealthService(db).get_system_status(experiment_id)
    return success(result)
