from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.core.response import success
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["工作台"])


@router.get("/summary")
def dashboard_summary(db: DbSession, _: CurrentUser):
    result = DashboardService(db).get_summary()
    return success(result.model_dump(by_alias=True))


@router.get("/reservation-status")
def reservation_status(db: DbSession, _: CurrentUser):
    items = DashboardService(db).reservation_status_distribution()
    return success([i.model_dump() for i in items])


@router.get("/resource-status")
def resource_status(db: DbSession, _: CurrentUser):
    items = DashboardService(db).resource_status_distribution()
    return success([i.model_dump() for i in items])


@router.get("/alarm-trend")
def alarm_trend(db: DbSession, _: CurrentUser):
    items = DashboardService(db).alarm_trend()
    return success([i.model_dump() for i in items])
