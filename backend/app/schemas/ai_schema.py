from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


ANALYSIS_TYPES = ("OVERVIEW", "ANOMALY", "RISK", "SUGGESTION")


class AiGenerateRequest(BaseModel):
    experiment_id: int = Field(..., alias="experimentId")
    analysis_type: str = Field("OVERVIEW", alias="analysisType")

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
    analysis_type: Optional[str] = Field(None, serialization_alias="analysisType")
    analysis_mode: Optional[str] = Field(None, serialization_alias="analysisMode")

    model_config = {"from_attributes": True, "populate_by_name": True}
