from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, DbSession, require_roles
from app.core.response import success
from app.models.user import SysUser
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/audit", tags=["审计日志"])

AdminUser = Annotated[SysUser, Depends(require_roles("ADMIN"))]


@router.get("/logs")
def list_operation_logs(
    db: DbSession,
    _: AdminUser,
    module: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[int] = Query(None, alias="userId"),
    keyword: Optional[str] = None,
    success: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
):
    result = AuditService(db).list_logs(
        module, action, user_id, keyword, success, page, page_size
    )
    return success(result.model_dump(by_alias=True))


@router.get("/meta")
def audit_meta(_: AdminUser):
    from app.schemas.audit_schema import ACTION_LABELS, MODULE_LABELS

    return success(
        {
            "modules": [{"value": k, "label": v} for k, v in MODULE_LABELS.items()],
            "actions": [{"value": k, "label": v} for k, v in ACTION_LABELS.items()],
        }
    )
