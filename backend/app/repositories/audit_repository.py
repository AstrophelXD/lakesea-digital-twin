from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.audit import SysOperationLog


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, log: SysOperationLog) -> SysOperationLog:
        self.db.add(log)
        self.db.flush()
        return log

    def list_logs(
        self,
        module: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        keyword: Optional[str] = None,
        success: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[SysOperationLog], int]:
        stmt = select(SysOperationLog).order_by(SysOperationLog.create_time.desc())
        if module:
            stmt = stmt.where(SysOperationLog.module == module)
        if action:
            stmt = stmt.where(SysOperationLog.action == action)
        if user_id is not None:
            stmt = stmt.where(SysOperationLog.user_id == user_id)
        if success is not None:
            stmt = stmt.where(SysOperationLog.success == (1 if success else 0))
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(
                or_(
                    SysOperationLog.username.like(like),
                    SysOperationLog.detail.like(like),
                    SysOperationLog.target_type.like(like),
                )
            )
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(
            self.db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
        )
        return items, total
