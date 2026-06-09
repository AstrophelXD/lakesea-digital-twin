from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.schemas.auth_schema import LoginRequest, LoginResponse, ProfileResponse, UserInfo

# 角色 → 前端菜单路由 name 列表
ROLE_MENUS: dict[str, list[str]] = {
    "ADMIN": [
        "dashboard",
        "users",
        "audit-logs",
        "resources",
        "reservations",
        "experiments",
        "monitor",
        "alarms",
        "archive",
        "ai-report",
    ],
    "DIRECTOR": [
        "dashboard",
        "resources",
        "reservations",
        "experiments",
        "monitor",
        "alarms",
        "archive",
        "ai-report",
    ],
    "TEACHER": [
        "dashboard",
        "resources",
        "reservations",
        "experiments",
        "monitor",
        "alarms",
        "archive",
        "ai-report",
    ],
    "STUDENT": [
        "dashboard",
        "resources",
        "reservations",
        "experiments",
        "monitor",
        "archive",
        "ai-report",
    ],
    "MAINTAINER": [
        "dashboard",
        "resources",
        "monitor",
        "alarms",
    ],
}


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def login(self, payload: LoginRequest) -> LoginResponse:
        audit = AuditService(self.db)
        user = self.repo.get_by_username(payload.username)
        if user is None or not verify_password(payload.password, user.password_hash):
            audit.log(
                "AUTH",
                "LOGIN",
                username=payload.username,
                success=False,
                detail="用户名或密码错误",
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名或密码错误",
            )
        if user.status != "ACTIVE":
            audit.log(
                "AUTH",
                "LOGIN",
                user_id=user.id,
                username=user.username,
                success=False,
                detail="账户已禁用",
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="账户已禁用",
            )
        roles = self.repo.get_role_codes(user.id)
        token = create_access_token(str(user.id), extra={"roles": roles})
        audit.log_user(user, "AUTH", "LOGIN", detail=f"角色: {','.join(roles)}")
        return LoginResponse(
            token=token,
            user=UserInfo(
                id=user.id,
                username=user.username,
                real_name=user.real_name,
                phone=user.phone,
                email=user.email,
                roles=roles,
            ),
        )

    def get_profile(self, user_id: int) -> ProfileResponse:
        user = self.repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
        roles = self.repo.get_role_codes(user_id)
        menus: list[str] = ["dashboard"]
        for role in roles:
            menus.extend(ROLE_MENUS.get(role, []))
        menus = list(dict.fromkeys(menus))  # 去重保序
        return ProfileResponse(
            user=UserInfo(
                id=user.id,
                username=user.username,
                real_name=user.real_name,
                phone=user.phone,
                email=user.email,
                roles=roles,
            ),
            menus=menus,
        )
