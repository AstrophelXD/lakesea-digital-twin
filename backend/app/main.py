import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.ai_api import reports_router as ai_reports_router
from app.api.ai_api import router as ai_router
from app.api.dashboard_api import router as dashboard_router
from app.api.health_api import router as health_router
from app.api.alarm_api import router as alarm_router
from app.api.file_api import router as file_router
from app.api.auth_api import router as auth_router
from app.api.experiment_api import router as experiment_router
from app.api.monitor_api import router as monitor_router
from app.api.reservation_api import router as reservation_router
from app.api.resource_api import router as resource_router
from app.api.user_api import router as user_router
from app.api.ws_monitor import router as ws_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.response import error


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 本地 SQLite：ORM 自动建表；达梦生产请执行 scripts/init_db.sql
    init_db()
    from app.services.mqtt_service import mqtt_service

    loop = asyncio.get_running_loop()
    mqtt_service.start(loop)
    yield
    mqtt_service.stop()


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(dashboard_router)
app.include_router(auth_router)
app.include_router(resource_router)
app.include_router(reservation_router)
app.include_router(experiment_router)
app.include_router(user_router)
app.include_router(monitor_router)
app.include_router(alarm_router)
app.include_router(ws_router)
app.include_router(file_router)
app.include_router(ai_router)
app.include_router(ai_reports_router)


@app.get("/api/health")
def health():
    return {"code": 200, "message": "ok", "data": {"status": "up"}}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code = exc.status_code if exc.status_code >= 400 else 400
    return JSONResponse(status_code=200, content=error(code, str(exc.detail)))


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    if settings.debug:
        message = str(exc)
    else:
        message = "服务器内部错误"
    return JSONResponse(status_code=200, content=error(500, message))
