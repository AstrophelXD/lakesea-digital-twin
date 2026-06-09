from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.core.response import success
from app.services.monitor_service import MonitorService
from app.services.mqtt_service import mqtt_service

router = APIRouter(prefix="/api/monitor", tags=["实时监控"])


@router.get("/mqtt/info")
def mqtt_info(_: CurrentUser):
    return success(mqtt_service.get_info().model_dump(by_alias=True))


@router.get("/{experiment_id}/status")
async def monitor_status(experiment_id: int, db: DbSession, _: CurrentUser):
    result = MonitorService(db).get_status(experiment_id)
    return success(result.model_dump(by_alias=True))


@router.post("/{experiment_id}/start")
async def start_monitor(experiment_id: int, db: DbSession, _: CurrentUser):
    svc = MonitorService(db)
    result = await svc.start_simulation(experiment_id)
    return success(result.model_dump(by_alias=True))


@router.post("/{experiment_id}/stop")
async def stop_monitor(experiment_id: int, db: DbSession, _: CurrentUser):
    svc = MonitorService(db)
    result = await svc.stop_simulation(experiment_id)
    return success(result.model_dump(by_alias=True))


@router.post("/{experiment_id}/demo-alarm")
async def trigger_demo_alarm(
    experiment_id: int,
    db: DbSession,
    _: CurrentUser,
    alarm_type: str = Query(..., alias="alarmType"),
):
    frame = await MonitorService(db).trigger_demo_alarm(experiment_id, alarm_type)
    return success(frame)


@router.get("/{experiment_id}/snapshot")
def monitor_snapshot(
    experiment_id: int,
    db: DbSession,
    _: CurrentUser,
    track_limit: int = Query(200, ge=1, le=1000, alias="trackLimit"),
):
    result = MonitorService(db).get_snapshot(experiment_id)
    return success(result.model_dump(by_alias=True))
