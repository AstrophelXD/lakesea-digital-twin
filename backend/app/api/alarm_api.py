from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, DbSession, require_roles
from app.core.response import success
from app.models.user import SysUser
from app.schemas.alarm_schema import AlarmHandleRequest
from app.services.alarm_service import AlarmService

router = APIRouter(prefix="/api/alarms", tags=["告警"])

HandlerUser = Annotated[SysUser, Depends(require_roles("ADMIN", "MAINTAINER", "DIRECTOR"))]


@router.get("")
def list_alarms(
    db: DbSession,
    _: CurrentUser,
    experiment_id: Optional[int] = Query(None, alias="experimentId"),
    handle_status: Optional[str] = Query(None, alias="handleStatus"),
    alarm_type: Optional[str] = Query(None, alias="alarmType"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
):
    result = AlarmService(db).list_alarms(
        experiment_id, handle_status, alarm_type, page, page_size
    )
    return success(result.model_dump(by_alias=True))


@router.post("/{alarm_id}/handle")
def handle_alarm(
    alarm_id: int,
    payload: AlarmHandleRequest,
    db: DbSession,
    current_user: HandlerUser,
):
    result = AlarmService(db).handle_alarm(alarm_id, payload, current_user)
    return success(result.model_dump(by_alias=True))
