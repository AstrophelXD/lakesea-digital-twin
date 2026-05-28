from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class MonitorFrame(BaseModel):
    experiment_id: int = Field(serialization_alias="experimentId")
    ship_code: str = Field(default="M-001", serialization_alias="shipCode")
    timestamp: str
    position: dict[str, float]
    speed: float
    heading: float
    roll: float
    pitch: float
    battery: float
    resistance: float
    alarm: Optional[dict[str, Any]] = None

    model_config = {"populate_by_name": True}


class MonitorStatusOut(BaseModel):
    experiment_id: int = Field(serialization_alias="experimentId")
    running: bool
    connected_clients: int = Field(serialization_alias="connectedClients")
    frame_count: int = Field(serialization_alias="frameCount")

    model_config = {"populate_by_name": True}


class SensorPointOut(BaseModel):
    timestamp: datetime
    position_x: Optional[float] = Field(None, serialization_alias="positionX")
    position_y: Optional[float] = Field(None, serialization_alias="positionY")
    speed: Optional[float] = None
    battery: Optional[float] = None
    resistance: Optional[float] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class TrackPointOut(BaseModel):
    timestamp: datetime
    position_x: Optional[float] = Field(None, serialization_alias="positionX")
    position_y: Optional[float] = Field(None, serialization_alias="positionY")
    heading: Optional[float] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class MonitorSnapshotOut(BaseModel):
    latest: Optional[MonitorFrame] = None
    tracks: List[TrackPointOut] = []
    recent_sensor: List[SensorPointOut] = Field(
        default_factory=list, serialization_alias="recentSensor"
    )

    model_config = {"populate_by_name": True}
