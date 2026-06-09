import json
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.device_command import DeviceCommandLog


class DeviceCommandRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, log: DeviceCommandLog) -> DeviceCommandLog:
        self.db.add(log)
        self.db.flush()
        return log

    def get_by_id(self, command_id: int) -> Optional[DeviceCommandLog]:
        return self.db.get(DeviceCommandLog, command_id)

    def list_by_device(
        self,
        device_id: str,
        experiment_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[DeviceCommandLog], int]:
        stmt = select(DeviceCommandLog).where(DeviceCommandLog.device_id == device_id)
        if experiment_id is not None:
            stmt = stmt.where(DeviceCommandLog.experiment_id == experiment_id)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(
            self.db.scalars(
                stmt.order_by(DeviceCommandLog.issued_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return items, total

    @staticmethod
    def payload_to_str(payload: Optional[dict]) -> Optional[str]:
        if payload is None:
            return None
        return json.dumps(payload, ensure_ascii=False)
