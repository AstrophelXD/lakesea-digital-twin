from fastapi import APIRouter

from app.core.deps import CurrentUser
from app.core.response import success
from app.services.cv_tracking_service import CvTrackingService

router = APIRouter(prefix="/api/cv", tags=["OpenCV 识别"])


@router.get("/{experiment_id}/status")
def cv_status(experiment_id: int, _: CurrentUser):
    result = CvTrackingService.get_status(experiment_id)
    return success(result.model_dump(by_alias=True))


@router.get("/{experiment_id}/track")
def cv_latest_track(experiment_id: int, _: CurrentUser):
    latest = CvTrackingService.get_latest(experiment_id)
    return success(latest.model_dump(by_alias=True) if latest else None)


@router.post("/{experiment_id}/start")
async def cv_start(experiment_id: int, _: CurrentUser):
    result = await CvTrackingService.start_tracking(experiment_id)
    return success(result.model_dump(by_alias=True))


@router.post("/{experiment_id}/stop")
async def cv_stop(experiment_id: int, _: CurrentUser):
    result = await CvTrackingService.stop_tracking(experiment_id)
    return success(result.model_dump(by_alias=True))
