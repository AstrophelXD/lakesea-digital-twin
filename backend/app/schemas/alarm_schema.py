from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AlarmOut(BaseModel):
    id: int
    experiment_id: int = Field(serialization_alias="experimentId")
    alarm_type: str = Field(serialization_alias="alarmType")
    alarm_level: Optional[str] = Field(None, serialization_alias="alarmLevel")
    alarm_message: Optional[str] = Field(None, serialization_alias="alarmMessage")
    handle_status: str = Field(serialization_alias="handleStatus")
    handler_id: Optional[int] = Field(None, serialization_alias="handlerId")
    handle_time: Optional[datetime] = Field(None, serialization_alias="handleTime")
    handle_comment: Optional[str] = Field(None, serialization_alias="handleComment")
    create_time: datetime = Field(serialization_alias="createTime")

    model_config = {"from_attributes": True, "populate_by_name": True}


class AlarmHandleRequest(BaseModel):
    handle_status: str = Field(..., alias="handleStatus")
    comment: Optional[str] = None

    model_config = {"populate_by_name": True}
