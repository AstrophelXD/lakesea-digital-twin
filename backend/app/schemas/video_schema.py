from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import PageResult


class VideoStreamConfigOut(BaseModel):
    mode: str
    camera_id: str = Field(serialization_alias="cameraId")
    stream_url: Optional[str] = Field(None, serialization_alias="streamUrl")
    file_url: Optional[str] = Field(None, serialization_alias="fileUrl")
    mjpeg_url: Optional[str] = Field(None, serialization_alias="mjpegUrl")
    status: str

    model_config = {"populate_by_name": True}


class VideoRecordOut(BaseModel):
    id: int
    experiment_id: int = Field(serialization_alias="experimentId")
    camera_id: str = Field(serialization_alias="cameraId")
    stream_url: Optional[str] = Field(None, serialization_alias="streamUrl")
    file_path: Optional[str] = Field(None, serialization_alias="filePath")
    start_time: Optional[datetime] = Field(None, serialization_alias="startTime")
    end_time: Optional[datetime] = Field(None, serialization_alias="endTime")
    status: str
    create_time: Optional[datetime] = Field(None, serialization_alias="createTime")

    model_config = {"from_attributes": True, "populate_by_name": True}


class VideoRecordStartRequest(BaseModel):
    camera_id: str = Field(default="CAM-001", alias="cameraId")
    mode: str = Field(default="file")

    model_config = {"populate_by_name": True}


class VideoRecordPageOut(PageResult[VideoRecordOut]):
    pass
