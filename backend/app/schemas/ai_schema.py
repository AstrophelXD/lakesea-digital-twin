from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AiGenerateRequest(BaseModel):
    experiment_id: int = Field(..., alias="experimentId")

    model_config = {"populate_by_name": True}


class AiReportOut(BaseModel):
    id: int
    experiment_id: int = Field(serialization_alias="experimentId")
    report_title: Optional[str] = Field(None, serialization_alias="reportTitle")
    summary_text: Optional[str] = Field(None, serialization_alias="summaryText")
    analysis_text: Optional[str] = Field(None, serialization_alias="analysisText")
    model_name: Optional[str] = Field(None, serialization_alias="modelName")
    generated_time: datetime = Field(serialization_alias="generatedTime")
    mock: bool = False

    model_config = {"from_attributes": True, "populate_by_name": True}
