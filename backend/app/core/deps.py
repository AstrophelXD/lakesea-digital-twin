from typing import Annotated, Callable, List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import SysUser
from app.repositories.user_repository import UserRepository

security_scheme = HTTPBearer(auto_error=False)
DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(security_scheme)
    ],
) -> SysUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
        )
    payload = decode_access_token(credentials.credentials)
    if payload is None or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或已过期的令牌",
        )
    user_id = int(payload["sub"])
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if user is None or user.is_deleted != 0 or user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用",
        )
    return user


CurrentUser = Annotated[SysUser, Depends(get_current_user)]


def require_roles(*allowed_roles: str) -> Callable:
    def checker(user: CurrentUser, db: DbSession) -> SysUser:
        repo = UserRepository(db)
        roles = repo.get_role_codes(user.id)
        if not any(r in allowed_roles for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足",
            )
        return user

    return checker
