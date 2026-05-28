from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession
from app.core.response import success
from app.models.user import SysRole, SysUser, SysUserRole

router = APIRouter(prefix="/api/users", tags=["用户"])


@router.get("/teachers")
def list_teachers(db: DbSession, _: CurrentUser):
    stmt = (
        select(SysUser.id, SysUser.username, SysUser.real_name)
        .join(SysUserRole, SysUserRole.user_id == SysUser.id)
        .join(SysRole, SysRole.id == SysUserRole.role_id)
        .where(SysRole.role_code == "TEACHER", SysUser.is_deleted == 0, SysUser.status == "ACTIVE")
    )
    rows = db.execute(stmt).all()
    data = [
        {"id": r.id, "username": r.username, "realName": r.real_name}
        for r in rows
    ]
    return success(data)
