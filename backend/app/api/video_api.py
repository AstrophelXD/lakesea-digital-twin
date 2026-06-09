import asyncio

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse, StreamingResponse

from app.core.deps import CurrentUser, DbSession
from app.core.response import success
from app.schemas.video_schema import VideoRecordStartRequest
from app.services.video_service import VideoService

router = APIRouter(prefix="/api/video", tags=["视频监控"])


@router.get("/{experiment_id}/config")
def video_config(experiment_id: int, db: DbSession, _: CurrentUser):
    result = VideoService(db).get_stream_config(experiment_id)
    return success(result.model_dump(by_alias=True))


@router.post("/{experiment_id}/start")
def start_video(
    experiment_id: int,
    payload: VideoRecordStartRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    result = VideoService(db).start_recording(
        experiment_id, payload.camera_id, payload.mode, current_user
    )
    return success(result.model_dump(by_alias=True))


@router.post("/{experiment_id}/stop")
def stop_video(experiment_id: int, db: DbSession, _: CurrentUser):
    result = VideoService(db).stop_recording(experiment_id)
    return success(result.model_dump(by_alias=True))


@router.get("/{experiment_id}/records")
def list_video_records(
    experiment_id: int,
    db: DbSession,
    _: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
):
    result = VideoService(db).list_records(experiment_id, page, page_size)
    return success(result.model_dump(by_alias=True))


@router.get("/{experiment_id}/demo-file")
def demo_video_file(experiment_id: int, db: DbSession):
    path = VideoService(db).resolve_demo_file(experiment_id)
    return FileResponse(path, media_type="video/mp4", filename="demo_pool.mp4")


@router.get("/{experiment_id}/mjpeg")
async def mjpeg_stream(experiment_id: int, db: DbSession):
    svc = VideoService(db)
    svc._ensure_experiment(experiment_id)

    async def generate():
        idx = 0
        while True:
            frame = svc.generate_synthetic_frame(idx)
            if not frame:
                await asyncio.sleep(0.5)
                idx += 1
                continue
            yield (
                b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            )
            idx += 1
            await asyncio.sleep(0.1)

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
