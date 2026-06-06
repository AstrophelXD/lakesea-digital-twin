from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.constants import (
    APPROVAL_APPROVED,
    APPROVAL_REJECTED,
    APPROVED,
    CANCELLED,
    DIRECTOR_APPROVAL,
    DRAFT,
    PENDING_DIRECTOR,
    PENDING_PREPARE,
    PENDING_TEACHER,
    REJECTED,
    TEACHER_REVIEW,
)
from app.models.experiment import ExperimentTask
from app.models.reservation import ExpApprovalLog, ExpReservation, ExpReservationResource
from app.models.user import SysUser
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.resource_repository import ResourceRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PageResult
from app.schemas.reservation_schema import (
    ApprovalLogOut,
    ApprovalRequest,
    ConflictCheckResult,
    ConflictItem,
    ReservationCreate,
    ReservationDetailOut,
    ReservationOut,
    ReservationResourceItem,
    ReservationResourceOut,
    ReservationUpdate,
)
from app.services.resource_service import ResourceService


def _gen_no(prefix: str) -> str:
    return f"{prefix}{datetime.now().strftime('%Y%m%d%H%M%S')}"


class ReservationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ReservationRepository(db)
        self.resource_repo = ResourceRepository(db)
        self.experiment_repo = ExperimentRepository(db)
        self.user_repo = UserRepository(db)
        self.resource_service = ResourceService(db)

    def _user_name(self, user_id: Optional[int]) -> Optional[str]:
        if not user_id:
            return None
        user = self.user_repo.get_by_id(user_id)
        return user.real_name if user else None

    def _to_out(self, r: ExpReservation) -> ReservationOut:
        return ReservationOut(
            id=r.id,
            reservation_no=r.reservation_no,
            exp_name=r.exp_name,
            exp_type=r.exp_type,
            applicant_id=r.applicant_id,
            applicant_name=self._user_name(r.applicant_id),
            teacher_id=r.teacher_id,
            teacher_name=self._user_name(r.teacher_id),
            start_time=r.start_time,
            end_time=r.end_time,
            status=r.status,
            purpose=r.purpose,
            plan_summary=r.plan_summary,
            submit_time=r.submit_time,
            reject_reason=r.reject_reason,
            create_time=r.create_time,
        )

    def _build_resources(
        self,
        reservation_id: int,
        items: List[ReservationResourceItem],
        default_start: datetime,
        default_end: datetime,
    ) -> List[ExpReservationResource]:
        rows: List[ExpReservationResource] = []
        for item in items:
            self.resource_service.ensure_bookable(item.resource_id)
            start = item.start_time or default_start
            end = item.end_time or default_end
            if end <= start:
                raise HTTPException(status_code=400, detail="资源占用结束时间必须晚于开始时间")
            rows.append(
                ExpReservationResource(
                    reservation_id=reservation_id,
                    resource_id=item.resource_id,
                    resource_type=item.resource_type,
                    quantity=item.quantity,
                    start_time=start,
                    end_time=end,
                    remark=item.remark,
                )
            )
        return rows

    def _collect_conflicts(
        self,
        items: List[ReservationResourceItem],
        exclude_reservation_id: Optional[int] = None,
    ) -> List[ConflictItem]:
        result: List[ConflictItem] = []
        for item in items:
            start = item.start_time
            end = item.end_time
            conflicts = self.repo.find_conflicts(
                item.resource_id, start, end, exclude_reservation_id
            )
            resource = self.resource_repo.get_by_id(item.resource_id)
            name = resource.resource_name if resource else str(item.resource_id)
            for c in conflicts:
                result.append(
                    ConflictItem(
                        resource_id=item.resource_id,
                        resource_name=name,
                        conflict_reservation_no=c.reservation_no,
                        conflict_exp_name=c.exp_name,
                        start_time=start,
                        end_time=end,
                    )
                )
        return result

    def _check_conflicts(
        self,
        items: List[ReservationResourceItem],
        exclude_reservation_id: Optional[int] = None,
    ) -> None:
        conflicts = self._collect_conflicts(items, exclude_reservation_id)
        if conflicts:
            first = conflicts[0]
            raise HTTPException(
                status_code=400,
                detail=(
                    f"资源「{first.resource_name}」在 {first.start_time} ~ {first.end_time} "
                    f"时段已被预约 {first.conflict_reservation_no} 占用"
                ),
            )

    def check_conflicts(
        self,
        reservation_id: int,
        current_user: SysUser,
        roles: List[str],
    ) -> ConflictCheckResult:
        reservation = self.repo.get_detail(reservation_id)
        if not reservation:
            raise HTTPException(status_code=404, detail="预约不存在")
        self._ensure_can_view(reservation, current_user, roles)
        items = [
            ReservationResourceItem(
                resource_id=rr.resource_id,
                resource_type=rr.resource_type,
                quantity=rr.quantity,
                start_time=rr.start_time,
                end_time=rr.end_time,
                remark=rr.remark,
            )
            for rr in reservation.resources
        ]
        conflicts = self._collect_conflicts(items, reservation_id)
        return ConflictCheckResult(has_conflict=len(conflicts) > 0, conflicts=conflicts)

    def list_reservations(
        self,
        current_user: SysUser,
        roles: List[str],
        status: Optional[str] = None,
        applicant_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PageResult[ReservationOut]:
        if "STUDENT" in roles and "ADMIN" not in roles and "DIRECTOR" not in roles and "TEACHER" not in roles:
            applicant_id = current_user.id
        elif "TEACHER" in roles and "ADMIN" not in roles and "DIRECTOR" not in roles:
            if teacher_id is None:
                teacher_id = current_user.id
        items, total = self.repo.list_reservations(
            status, applicant_id, teacher_id, keyword, page, page_size
        )
        return PageResult(
            items=[self._to_out(r) for r in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_detail(self, reservation_id: int, current_user: SysUser, roles: List[str]) -> ReservationDetailOut:
        reservation = self.repo.get_detail(reservation_id)
        if not reservation:
            raise HTTPException(status_code=404, detail="预约不存在")
        self._ensure_can_view(reservation, current_user, roles)
        base = self._to_out(reservation)
        resources_out: List[ReservationResourceOut] = []
        for rr in reservation.resources:
            lab = self.resource_repo.get_by_id(rr.resource_id)
            resources_out.append(
                ReservationResourceOut(
                    id=rr.id,
                    resource_id=rr.resource_id,
                    resource_type=rr.resource_type,
                    resource_name=lab.resource_name if lab else None,
                    quantity=rr.quantity,
                    start_time=rr.start_time,
                    end_time=rr.end_time,
                    remark=rr.remark,
                )
            )
        logs_out = [
            ApprovalLogOut(
                id=log.id,
                step_type=log.step_type,
                approver_id=log.approver_id,
                approver_name=self._user_name(log.approver_id),
                result=log.result,
                comment=log.comment,
                action_time=log.action_time,
            )
            for log in sorted(reservation.approval_logs, key=lambda x: x.action_time)
        ]
        task = self.experiment_repo.get_by_reservation_id(reservation_id)
        return ReservationDetailOut(
            **base.model_dump(),
            resources=resources_out,
            approval_logs=logs_out,
            experiment_task_id=task.id if task else None,
        )

    def _ensure_can_view(self, r: ExpReservation, user: SysUser, roles: List[str]) -> None:
        if "ADMIN" in roles or "DIRECTOR" in roles:
            return
        if "TEACHER" in roles and r.teacher_id == user.id:
            return
        if r.applicant_id == user.id:
            return
        raise HTTPException(status_code=403, detail="无权查看该预约")

    def create_draft(self, payload: ReservationCreate, applicant: SysUser) -> ReservationDetailOut:
        if not payload.resources:
            raise HTTPException(status_code=400, detail="请至少添加一条资源明细")
        teacher = self.user_repo.get_by_id(payload.teacher_id)
        if not teacher:
            raise HTTPException(status_code=400, detail="指导教师不存在")
        reservation = ExpReservation(
            reservation_no=_gen_no("RSV"),
            exp_name=payload.exp_name,
            exp_type=payload.exp_type,
            applicant_id=applicant.id,
            teacher_id=payload.teacher_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
            status=DRAFT,
            purpose=payload.purpose,
            plan_summary=payload.plan_summary,
            is_deleted=0,
        )
        self.repo.create(reservation)
        rows = self._build_resources(
            reservation.id, payload.resources, payload.start_time, payload.end_time
        )
        reservation.resources = rows
        self.db.commit()
        return self.get_detail(reservation.id, applicant, self.user_repo.get_role_codes(applicant.id))

    def update_draft(
        self, reservation_id: int, payload: ReservationUpdate, user: SysUser, roles: List[str]
    ) -> ReservationDetailOut:
        reservation = self.repo.get_detail(reservation_id)
        if not reservation:
            raise HTTPException(status_code=404, detail="预约不存在")
        if reservation.applicant_id != user.id and "ADMIN" not in roles:
            raise HTTPException(status_code=403, detail="仅申请人可修改")
        if reservation.status not in (DRAFT, REJECTED):
            raise HTTPException(status_code=400, detail="仅草稿或已驳回状态可修改")
        if not payload.resources:
            raise HTTPException(status_code=400, detail="请至少添加一条资源明细")

        reservation.exp_name = payload.exp_name
        reservation.exp_type = payload.exp_type
        reservation.teacher_id = payload.teacher_id
        reservation.start_time = payload.start_time
        reservation.end_time = payload.end_time
        reservation.purpose = payload.purpose
        reservation.plan_summary = payload.plan_summary

        self.repo.delete_resources_by_reservation(reservation_id)
        reservation.resources = self._build_resources(
            reservation_id, payload.resources, payload.start_time, payload.end_time
        )
        self.db.commit()
        return self.get_detail(reservation_id, user, roles)

    def submit(self, reservation_id: int, user: SysUser, roles: List[str]) -> ReservationDetailOut:
        reservation = self.repo.get_detail(reservation_id)
        if not reservation:
            raise HTTPException(status_code=404, detail="预约不存在")
        if reservation.applicant_id != user.id and "ADMIN" not in roles:
            raise HTTPException(status_code=403, detail="仅申请人可提交")
        if reservation.status not in (DRAFT, REJECTED):
            raise HTTPException(status_code=400, detail="当前状态不可提交")

        items = [
            ReservationResourceItem(
                resource_id=rr.resource_id,
                resource_type=rr.resource_type,
                quantity=rr.quantity,
                start_time=rr.start_time,
                end_time=rr.end_time,
                remark=rr.remark,
            )
            for rr in reservation.resources
        ]
        self._check_conflicts(items, reservation_id)
        reservation.status = PENDING_TEACHER
        reservation.submit_time = datetime.now()
        reservation.reject_reason = None
        self.db.commit()
        return self.get_detail(reservation_id, user, roles)

    def teacher_review(
        self, reservation_id: int, payload: ApprovalRequest, user: SysUser, roles: List[str]
    ) -> ReservationDetailOut:
        reservation = self.repo.get_by_id(reservation_id)
        if not reservation:
            raise HTTPException(status_code=404, detail="预约不存在")
        if reservation.status != PENDING_TEACHER:
            raise HTTPException(status_code=400, detail="当前状态不允许教师审核")
        if "ADMIN" not in roles:
            if reservation.teacher_id != user.id:
                raise HTTPException(status_code=403, detail="只能审核分配给自己的预约")
            if reservation.applicant_id == user.id:
                raise HTTPException(status_code=403, detail="不能审核自己提交的预约")

        if not payload.approved and not payload.comment:
            raise HTTPException(status_code=400, detail="驳回必须填写原因")

        now = datetime.now()
        if payload.approved:
            reservation.status = PENDING_DIRECTOR
            reservation.teacher_review_by = user.id
            reservation.teacher_review_time = now
            reservation.teacher_review_comment = payload.comment
            result = APPROVAL_APPROVED
        else:
            reservation.status = REJECTED
            reservation.reject_reason = payload.comment
            result = APPROVAL_REJECTED

        self.repo.add_approval_log(
            ExpApprovalLog(
                reservation_id=reservation_id,
                step_type=TEACHER_REVIEW,
                approver_id=user.id,
                result=result,
                comment=payload.comment,
                action_time=now,
            )
        )
        self.db.commit()
        return self.get_detail(reservation_id, user, roles)

    def director_approve(
        self, reservation_id: int, payload: ApprovalRequest, user: SysUser, roles: List[str]
    ) -> ReservationDetailOut:
        if "DIRECTOR" not in roles and "ADMIN" not in roles:
            raise HTTPException(status_code=403, detail="仅主任或管理员可审批")

        reservation = self.repo.get_detail(reservation_id)
        if not reservation:
            raise HTTPException(status_code=404, detail="预约不存在")
        if reservation.status != PENDING_DIRECTOR:
            raise HTTPException(status_code=400, detail="当前状态不允许主任审批")
        if not payload.approved and not payload.comment:
            raise HTTPException(status_code=400, detail="驳回必须填写原因")

        now = datetime.now()
        if payload.approved:
            items = [
                ReservationResourceItem(
                    resource_id=rr.resource_id,
                    resource_type=rr.resource_type,
                    quantity=rr.quantity,
                    start_time=rr.start_time,
                    end_time=rr.end_time,
                )
                for rr in reservation.resources
            ]
            self._check_conflicts(items, reservation_id)
            reservation.status = APPROVED
            reservation.director_approved_by = user.id
            reservation.director_approved_time = now
            reservation.director_approval_comment = payload.comment
            result = APPROVAL_APPROVED

            task = ExperimentTask(
                task_no=_gen_no("TASK"),
                reservation_id=reservation.id,
                exp_name=reservation.exp_name,
                status=PENDING_PREPARE,
                is_deleted=0,
            )
            self.experiment_repo.create(task)
        else:
            reservation.status = REJECTED
            reservation.reject_reason = payload.comment
            result = APPROVAL_REJECTED

        self.repo.add_approval_log(
            ExpApprovalLog(
                reservation_id=reservation_id,
                step_type=DIRECTOR_APPROVAL,
                approver_id=user.id,
                result=result,
                comment=payload.comment,
                action_time=now,
            )
        )
        self.db.commit()
        return self.get_detail(reservation_id, user, roles)

    def cancel(self, reservation_id: int, user: SysUser, roles: List[str]) -> ReservationDetailOut:
        reservation = self.repo.get_by_id(reservation_id)
        if not reservation:
            raise HTTPException(status_code=404, detail="预约不存在")
        if reservation.applicant_id != user.id and "ADMIN" not in roles:
            raise HTTPException(status_code=403, detail="仅申请人可取消")
        if reservation.status not in (PENDING_TEACHER, PENDING_DIRECTOR):
            raise HTTPException(status_code=400, detail="当前状态不可取消")
        reservation.status = CANCELLED
        self.db.commit()
        return self.get_detail(reservation_id, user, roles)
