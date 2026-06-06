from typing import List

from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    today_reservations: int = Field(serialization_alias="todayReservations")
    running_experiments: int = Field(serialization_alias="runningExperiments")
    available_resources: int = Field(serialization_alias="availableResources")
    pending_alarms: int = Field(serialization_alias="pendingAlarms")
    database_type: str = Field(serialization_alias="databaseType")

    model_config = {"populate_by_name": True}


class StatusCount(BaseModel):
    status: str
    count: int


class TrendPoint(BaseModel):
    date: str
    count: int
