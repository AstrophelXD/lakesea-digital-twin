from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CvTrackResult(BaseModel):
    experiment_id: int = Field(serialization_alias="experimentId")
    camera_id: str = Field(serialization_alias="cameraId")
    timestamp: str
    bbox: List[float]
    center_x: float = Field(serialization_alias="centerX")
    center_y: float = Field(serialization_alias="centerY")
    pool_x: float = Field(serialization_alias="poolX")
    pool_y: float = Field(serialization_alias="poolY")
    confidence: float
    source: str = "simulation"

    model_config = {"populate_by_name": True}


class CvTrackStatusOut(BaseModel):
    enabled: bool
    opencv_available: bool = Field(serialization_alias="opencvAvailable")
    tracking: bool
    latest: Optional[CvTrackResult] = None

    model_config = {"populate_by_name": True}
