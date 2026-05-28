from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ExperimentOut(BaseModel):
    id: int
    task_no: str = Field(serialization_alias="taskNo")
    reservation_id: int = Field(serialization_alias="reservationId")
    exp_name: str = Field(serialization_alias="expName")
    status: str
    actual_start_time: Optional[datetime] = Field(None, serialization_alias="actualStartTime")
    actual_end_time: Optional[datetime] = Field(None, serialization_alias="actualEndTime")
    create_time: Optional[datetime] = Field(None, serialization_alias="createTime")

    model_config = {"from_attributes": True, "populate_by_name": True}
