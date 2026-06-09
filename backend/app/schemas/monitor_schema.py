from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


class MonitorFrame(BaseModel):
    experiment_id: int = Field(serialization_alias="experimentId")
    ship_code: str = Field(default="M-001", serialization_alias="shipCode")
    timestamp: str
    server_time: Optional[str] = Field(None, serialization_alias="serverTime")
    position: dict[str, float]
    speed: float
    heading: float
    roll: float
    pitch: float
    battery: float
    resistance: float
    alarm: Optional[dict[str, Any]] = None
    cv_track: Optional[dict[str, Any]] = Field(None, serialization_alias="cvTrack")

    model_config = {"populate_by_name": True}


class MonitorStatusOut(BaseModel):
    experiment_id: int = Field(serialization_alias="experimentId")
    running: bool
    connected_clients: int = Field(serialization_alias="connectedClients")
    frame_count: int = Field(serialization_alias="frameCount")
    data_source: str = Field("websocket_sim", serialization_alias="dataSource")
    mqtt_connected: Optional[bool] = Field(None, serialization_alias="mqttConnected")

    model_config = {"populate_by_name": True}


class MqttPosition(BaseModel):
    x: float
    y: float


class MqttSensorPayload(BaseModel):
    experiment_id: Optional[int] = Field(None, alias="experimentId")
    ship_code: str = Field("M-001", alias="shipCode")
    timestamp: datetime | str
    position: MqttPosition
    speed: float
    heading: float
    roll: float = 0.0
    pitch: float = 0.0
    battery: float
    resistance: float

    model_config = {"populate_by_name": True}

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, value: Any) -> datetime | str:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            return value
        return value


class MqttInfoOut(BaseModel):
    enabled: bool
    connected: bool
    broker_host: str = Field(serialization_alias="brokerHost")
    broker_port: int = Field(serialization_alias="brokerPort")
    topic_prefix: str = Field(serialization_alias="topicPrefix")
    subscribed_topic: str = Field(serialization_alias="subscribedTopic")
    data_source: str = Field(serialization_alias="dataSource")

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
