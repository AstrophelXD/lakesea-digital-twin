from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.alarm_repository import AlarmRepository
from app.schemas.alarm_schema import AlarmHandleRequest, AlarmOut
from app.schemas.common import PageResult


class AlarmService:
    def __init__(self, db: Session) -> None:
        self.repo = AlarmRepository(db)
        self.db = db

    def list_alarms(
        self,
        experiment_id: Optional[int] = None,
        handle_status: Optional[str] = None,
        alarm_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PageResult[AlarmOut]:
        items, total = self.repo.list_alarms(
            experiment_id, handle_status, alarm_type, page, page_size
        )
        return PageResult(
            items=[AlarmOut.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def handle_alarm(
        self, alarm_id: int, payload: AlarmHandleRequest, handler_id: int
    ) -> AlarmOut:
        alarm = self.repo.get_by_id(alarm_id)
        if not alarm:
            raise HTTPException(status_code=404, detail="告警不存在")
        alarm.handle_status = payload.handle_status
        alarm.handle_comment = payload.comment
        alarm.handler_id = handler_id
        alarm.handle_time = datetime.now()
        self.db.commit()
        self.db.refresh(alarm)
        return AlarmOut.model_validate(alarm)
