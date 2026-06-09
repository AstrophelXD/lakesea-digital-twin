from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import PageResult

ANALYSIS_TYPES = ("OVERVIEW", "ANOMALY", "RISK", "SUGGESTION")

ANALYSIS_TYPE_LABELS = {
    "OVERVIEW": "试验概况摘要",
    "ANOMALY": "异常原因分析",
    "RISK": "风险提示",
    "SUGGESTION": "后续试验建议",
}


class AiGenerateRequest(BaseModel):
    experiment_id: int = Field(..., alias="experimentId")
    analysis_type: str = Field("OVERVIEW", alias="analysisType")

    model_config = {"populate_by_name": True}


class ReportSection(BaseModel):
    title: str
    content: str


class AlarmBrief(BaseModel):
    alarm_type: str = Field(serialization_alias="alarmType")
    alarm_message: Optional[str] = Field(None, serialization_alias="alarmMessage")
    create_time: datetime = Field(serialization_alias="createTime")

    model_config = {"populate_by_name": True}


class ExperimentDataSummary(BaseModel):
    experiment_id: int = Field(serialization_alias="experimentId")
    task_no: str = Field(serialization_alias="taskNo")
    exp_name: str = Field(serialization_alias="expName")
    status: str
    point_count: int = Field(serialization_alias="pointCount")
    max_speed: Optional[float] = Field(None, serialization_alias="maxSpeed")
    min_battery: Optional[float] = Field(None, serialization_alias="minBattery")
    max_resistance: Optional[float] = Field(None, serialization_alias="maxResistance")
    max_roll: Optional[float] = Field(None, serialization_alias="maxRoll")
    alarm_count: int = Field(serialization_alias="alarmCount")
    alarm_summary: str = Field(serialization_alias="alarmSummary")
    alarms: List[AlarmBrief] = []
    actual_start_time: Optional[datetime] = Field(None, serialization_alias="actualStartTime")
    actual_end_time: Optional[datetime] = Field(None, serialization_alias="actualEndTime")

    model_config = {"populate_by_name": True}


class AiModeOut(BaseModel):
    analysis_mode: str = Field(serialization_alias="analysisMode")
    mock_ai: bool = Field(serialization_alias="mockAi")
    has_api_key: bool = Field(serialization_alias="hasApiKey")
    model_name: str = Field(serialization_alias="modelName")

    model_config = {"populate_by_name": True}


class AiCallLogOut(BaseModel):
    id: int
    experiment_id: Optional[int] = Field(None, serialization_alias="experimentId")
    analysis_type: Optional[str] = Field(None, serialization_alias="analysisType")
    model_name: Optional[str] = Field(None, serialization_alias="modelName")
    is_mock: bool = Field(serialization_alias="isMock")
    success: bool
    duration_ms: Optional[int] = Field(None, serialization_alias="durationMs")
    token_used: Optional[int] = Field(None, serialization_alias="tokenUsed")
    error_message: Optional[str] = Field(None, serialization_alias="errorMessage")
    call_time: datetime = Field(serialization_alias="callTime")

    model_config = {"from_attributes": True, "populate_by_name": True}


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
    analysis_type_label: Optional[str] = Field(None, serialization_alias="analysisTypeLabel")
    analysis_mode: Optional[str] = Field(None, serialization_alias="analysisMode")
    sections: List[ReportSection] = []

    model_config = {"from_attributes": True, "populate_by_name": True}


class AiReportListItem(BaseModel):
    id: int
    experiment_id: int = Field(serialization_alias="experimentId")
    report_title: Optional[str] = Field(None, serialization_alias="reportTitle")
    analysis_type: Optional[str] = Field(None, serialization_alias="analysisType")
    model_name: Optional[str] = Field(None, serialization_alias="modelName")
    generated_time: datetime = Field(serialization_alias="generatedTime")

    model_config = {"from_attributes": True, "populate_by_name": True}
