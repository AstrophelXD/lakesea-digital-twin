from typing import Optional

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.core.response import success
from app.schemas.ai_schema import AiGenerateRequest
from app.services.ai_service import AiService

router = APIRouter(prefix="/api/ai", tags=["AI 分析"])


@router.get("/mode")
def get_ai_mode(db: DbSession, _: CurrentUser):
    return success(AiService(db).get_mode().model_dump(by_alias=True))


@router.get("/logs")
def list_ai_logs(
    db: DbSession,
    _: CurrentUser,
    experiment_id: Optional[int] = Query(None, alias="experimentId"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
):
    result = AiService(db).list_call_logs(experiment_id, page, page_size)
    return success(result.model_dump(by_alias=True))


reports_router = APIRouter(prefix="/api/ai/reports", tags=["AI 报告"])


@reports_router.get("/list")
def list_reports(
    db: DbSession,
    _: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
):
    result = AiService(db).list_reports(page, page_size)
    return success(result.model_dump(by_alias=True))


@reports_router.get("/summary/{experiment_id}")
def experiment_data_summary(experiment_id: int, db: DbSession, _: CurrentUser):
    result = AiService(db).get_data_summary(experiment_id)
    return success(result.model_dump(by_alias=True))


@reports_router.post("/generate")
async def generate_report(payload: AiGenerateRequest, db: DbSession, current_user: CurrentUser):
    result = await AiService(db).generate(
        payload.experiment_id, current_user.id, payload.analysis_type
    )
    return success(result.model_dump(by_alias=True))


@reports_router.get("/{experiment_id}")
def get_report(experiment_id: int, db: DbSession, _: CurrentUser):
    result = AiService(db).get_report(experiment_id)
    return success(result.model_dump(by_alias=True))


@reports_router.delete("/{report_id}")
def delete_report(report_id: int, db: DbSession, _: CurrentUser):
    AiService(db).delete_report(report_id)
    return success(message="报告已删除")
