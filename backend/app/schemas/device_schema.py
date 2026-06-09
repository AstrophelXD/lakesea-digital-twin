from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import PageResult


class DeviceInfoOut(BaseModel):
    device_id: str = Field(serialization_alias="deviceId")
    device_name: str = Field(serialization_alias="deviceName")
    device_type: str = Field(serialization_alias="deviceType")
    status: str
    online: bool
    last_command_type: Optional[str] = Field(None, serialization_alias="lastCommandType")
    last_ack_at: Optional[str] = Field(None, serialization_alias="lastAckAt")
    ack_status: Optional[str] = Field(None, serialization_alias="ackStatus")

    model_config = {"populate_by_name": True}


class DeviceCommandRequest(BaseModel):
    command_type: str = Field(alias="commandType")
    payload: Optional[dict[str, Any]] = None

    model_config = {"populate_by_name": True}


class DeviceCommandOut(BaseModel):
    id: int
    device_id: str = Field(serialization_alias="deviceId")
    experiment_id: Optional[int] = Field(None, serialization_alias="experimentId")
    command_type: str = Field(serialization_alias="commandType")
    command_payload: Optional[str] = Field(None, serialization_alias="commandPayload")
    issued_by: Optional[int] = Field(None, serialization_alias="issuedBy")
    issued_at: datetime = Field(serialization_alias="issuedAt")
    status: str
    result_message: Optional[str] = Field(None, serialization_alias="resultMessage")

    model_config = {"from_attributes": True, "populate_by_name": True}


class DeviceCommandPageOut(PageResult[DeviceCommandOut]):
    pass
