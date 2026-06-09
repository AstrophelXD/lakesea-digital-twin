from typing import Optional

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.core.response import success
from app.schemas.device_schema import DeviceCommandRequest
from app.services.device_command_service import DeviceCommandService

router = APIRouter(prefix="/api/devices", tags=["设备控制"])


@router.get("")
def list_devices(
    db: DbSession,
    _: CurrentUser,
    experiment_id: Optional[int] = Query(None, alias="experimentId"),
):
    items = DeviceCommandService(db).list_devices(experiment_id)
    return success([i.model_dump(by_alias=True) for i in items])


@router.post("/{device_id}/commands")
def issue_command(
    device_id: str,
    payload: DeviceCommandRequest,
    db: DbSession,
    current_user: CurrentUser,
    experiment_id: Optional[int] = Query(None, alias="experimentId"),
):
    result = DeviceCommandService(db).issue_command(
        device_id,
        payload.command_type,
        payload.payload,
        current_user,
        experiment_id,
    )
    return success(result.model_dump(by_alias=True))


@router.get("/{device_id}/commands")
def list_commands(
    device_id: str,
    db: DbSession,
    _: CurrentUser,
    experiment_id: Optional[int] = Query(None, alias="experimentId"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
):
    result = DeviceCommandService(db).list_commands(
        device_id, experiment_id, page, page_size
    )
    return success(result.model_dump(by_alias=True))


@router.post("/{device_id}/emergency-stop")
def emergency_stop(
    device_id: str,
    db: DbSession,
    current_user: CurrentUser,
    experiment_id: Optional[int] = Query(None, alias="experimentId"),
):
    result = DeviceCommandService(db).emergency_stop(
        device_id, current_user, experiment_id
    )
    return success(result.model_dump(by_alias=True))
