from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.alarm_schema import AlarmOut
from app.schemas.experiment_schema import ExperimentOut


class ReplayStats(BaseModel):
    point_count: int = Field(serialization_alias="pointCount")
    max_speed: Optional[float] = Field(None, serialization_alias="maxSpeed")
    min_battery: Optional[float] = Field(None, serialization_alias="minBattery")
    max_resistance: Optional[float] = Field(None, serialization_alias="maxResistance")
    alarm_count: int = Field(serialization_alias="alarmCount")

    model_config = {"populate_by_name": True}


class ReplayTrackPoint(BaseModel):
    timestamp: datetime
    position_x: float = Field(serialization_alias="positionX")
    position_y: float = Field(serialization_alias="positionY")
    heading: Optional[float] = None

    model_config = {"populate_by_name": True}


class ReplaySensorPoint(BaseModel):
    timestamp: datetime
    speed: Optional[float] = None
    battery: Optional[float] = None
    resistance: Optional[float] = None
    roll: Optional[float] = None

    model_config = {"from_attributes": True}


class ExperimentFileOut(BaseModel):
    id: int
    experiment_id: int = Field(serialization_alias="experimentId")
    file_name: str = Field(serialization_alias="fileName")
    file_type: Optional[str] = Field(None, serialization_alias="fileType")
    upload_time: datetime = Field(serialization_alias="uploadTime")

    model_config = {"from_attributes": True, "populate_by_name": True}


class ExperimentReplayOut(BaseModel):
    task: ExperimentOut
    tracks: List[ReplayTrackPoint] = []
    sensor_series: List[ReplaySensorPoint] = Field(
        default_factory=list, serialization_alias="sensorSeries"
    )
    alarms: List[AlarmOut] = []
    files: List[ExperimentFileOut] = []
    stats: ReplayStats

    model_config = {"populate_by_name": True}
