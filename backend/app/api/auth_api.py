from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.core.response import success
from app.schemas.auth_schema import LoginRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login")
def login(payload: LoginRequest, db: DbSession):
    result = AuthService(db).login(payload)
    return success(result.model_dump(by_alias=True))


@router.get("/profile")
def profile(current_user: CurrentUser, db: DbSession):
    result = AuthService(db).get_profile(current_user.id)
    return success(result.model_dump(by_alias=True))


@router.post("/logout")
def logout():
    # JWT 无状态，客户端清除 Token 即可
    return success(message="已退出登录")
