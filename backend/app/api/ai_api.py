from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.core.response import success
from app.schemas.ai_schema import AiGenerateRequest
from app.services.ai_service import AiService

router = APIRouter(prefix="/api/ai/reports", tags=["AI 分析"])


@router.post("/generate")
async def generate_report(payload: AiGenerateRequest, db: DbSession, current_user: CurrentUser):
    result = await AiService(db).generate(
        payload.experiment_id, current_user.id, payload.analysis_type
    )
    return success(result.model_dump(by_alias=True))


@router.get("/{experiment_id}")
def get_report(experiment_id: int, db: DbSession, _: CurrentUser):
    result = AiService(db).get_report(experiment_id)
    return success(result.model_dump(by_alias=True))


@router.delete("/{report_id}")
def delete_report(report_id: int, db: DbSession, _: CurrentUser):
    AiService(db).delete_report(report_id)
    return success(message="报告已删除")
