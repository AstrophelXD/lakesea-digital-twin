from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class ReservationResourceItem(BaseModel):
    resource_id: int = Field(..., alias="resourceId")
    resource_type: Optional[str] = Field(None, alias="resourceType")
    quantity: int = 1
    start_time: datetime = Field(..., alias="startTime")
    end_time: datetime = Field(..., alias="endTime")
    remark: Optional[str] = None

    model_config = {"populate_by_name": True}


class ReservationCreate(BaseModel):
    exp_name: str = Field(..., alias="expName", max_length=100)
    exp_type: Optional[str] = Field(None, alias="expType")
    teacher_id: int = Field(..., alias="teacherId")
    start_time: datetime = Field(..., alias="startTime")
    end_time: datetime = Field(..., alias="endTime")
    purpose: Optional[str] = None
    plan_summary: Optional[str] = Field(None, alias="planSummary")
    resources: List[ReservationResourceItem] = []

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def end_after_start(self):
        if self.end_time <= self.start_time:
            raise ValueError("结束时间必须晚于开始时间")
        return self


class ReservationUpdate(ReservationCreate):
    pass


class ApprovalRequest(BaseModel):
    approved: bool
    comment: Optional[str] = None


class ReservationResourceOut(BaseModel):
    id: int
    resource_id: int = Field(serialization_alias="resourceId")
    resource_type: Optional[str] = Field(None, serialization_alias="resourceType")
    resource_name: Optional[str] = Field(None, serialization_alias="resourceName")
    quantity: int
    start_time: datetime = Field(serialization_alias="startTime")
    end_time: datetime = Field(serialization_alias="endTime")
    remark: Optional[str] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class ApprovalLogOut(BaseModel):
    id: int
    step_type: str = Field(serialization_alias="stepType")
    approver_id: int = Field(serialization_alias="approverId")
    approver_name: Optional[str] = Field(None, serialization_alias="approverName")
    result: str
    comment: Optional[str] = None
    action_time: datetime = Field(serialization_alias="actionTime")

    model_config = {"from_attributes": True, "populate_by_name": True}


class ReservationOut(BaseModel):
    id: int
    reservation_no: str = Field(serialization_alias="reservationNo")
    exp_name: str = Field(serialization_alias="expName")
    exp_type: Optional[str] = Field(None, serialization_alias="expType")
    applicant_id: int = Field(serialization_alias="applicantId")
    applicant_name: Optional[str] = Field(None, serialization_alias="applicantName")
    teacher_id: Optional[int] = Field(None, serialization_alias="teacherId")
    teacher_name: Optional[str] = Field(None, serialization_alias="teacherName")
    start_time: datetime = Field(serialization_alias="startTime")
    end_time: datetime = Field(serialization_alias="endTime")
    status: str
    purpose: Optional[str] = None
    plan_summary: Optional[str] = Field(None, serialization_alias="planSummary")
    submit_time: Optional[datetime] = Field(None, serialization_alias="submitTime")
    reject_reason: Optional[str] = Field(None, serialization_alias="rejectReason")
    create_time: Optional[datetime] = Field(None, serialization_alias="createTime")

    model_config = {"from_attributes": True, "populate_by_name": True}


class ConflictItem(BaseModel):
    resource_id: int = Field(serialization_alias="resourceId")
    resource_name: Optional[str] = Field(None, serialization_alias="resourceName")
    conflict_reservation_no: str = Field(serialization_alias="conflictReservationNo")
    conflict_exp_name: str = Field(serialization_alias="conflictExpName")
    start_time: datetime = Field(serialization_alias="startTime")
    end_time: datetime = Field(serialization_alias="endTime")

    model_config = {"populate_by_name": True}


class ConflictCheckResult(BaseModel):
    has_conflict: bool = Field(serialization_alias="hasConflict")
    conflicts: List[ConflictItem] = []

    model_config = {"populate_by_name": True}


class ReservationDetailOut(ReservationOut):
    resources: List[ReservationResourceOut] = []
    approval_logs: List[ApprovalLogOut] = Field(default_factory=list, serialization_alias="approvalLogs")
    experiment_task_id: Optional[int] = Field(None, serialization_alias="experimentTaskId")

    model_config = {"from_attributes": True, "populate_by_name": True}
