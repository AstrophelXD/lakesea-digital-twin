from fastapi import APIRouter

from app.core.config import get_settings
from app.core.database import engine
from app.core.db_info import check_db_health
from app.core.response import success

router = APIRouter(prefix="/api/health", tags=["健康检查"])


@router.get("/db")
def db_health():
    settings = get_settings()
    result = check_db_health(engine, settings.database_url)
    return success(result.to_dict())
