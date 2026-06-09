import functools
import inspect
from typing import Any, Callable, List, Optional

from sqlalchemy.orm import Session

from app.core.audit_context import get_request_ip
from app.models.audit import SysOperationLog
from app.models.user import SysUser
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit_schema import ACTION_LABELS, MODULE_LABELS, OperationLogOut
from app.schemas.common import PageResult


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AuditRepository(db)

    def log(
        self,
        module: str,
        action: str,
        *,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        detail: Optional[str] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
    ) -> None:
        entry = SysOperationLog(
            user_id=user_id,
            username=username,
            module=module,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            ip_address=ip_address or get_request_ip(),
            success=1 if success else 0,
        )
        self.repo.create(entry)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def log_user(
        self,
        user: SysUser,
        module: str,
        action: str,
        *,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        detail: Optional[str] = None,
        success: bool = True,
    ) -> None:
        self.log(
            module,
            action,
            user_id=user.id,
            username=user.username,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            success=success,
        )

    def list_logs(
        self,
        module: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        keyword: Optional[str] = None,
        success: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PageResult[OperationLogOut]:
        items, total = self.repo.list_logs(
            module, action, user_id, keyword, success, page, page_size
        )
        return PageResult(
            items=[self._to_out(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def _to_out(self, log: SysOperationLog) -> OperationLogOut:
        out = OperationLogOut.model_validate(log)
        out.module_label = MODULE_LABELS.get(log.module, log.module)
        out.action_label = ACTION_LABELS.get(log.action, log.action)
        out.success = log.success == 1
        return out


def audited(
    module: str,
    action: str,
    target_type: Optional[str] = None,
) -> Callable:
    """API 层装饰器：成功执行后写入审计日志（需 db 与 current_user 参数）。"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)
            _write_audit(kwargs, module, action, target_type)
            return result

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            _write_audit(kwargs, module, action, target_type)
            return result

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def _write_audit(
    kwargs: dict[str, Any],
    module: str,
    action: str,
    target_type: Optional[str],
) -> None:
    db = kwargs.get("db")
    user = kwargs.get("current_user")
    if db is None or user is None:
        return
    AuditService(db).log_user(user, module, action, target_type=target_type)
