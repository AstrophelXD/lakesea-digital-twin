from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, DbSession, require_roles
from app.models.user import SysUser
from app.core.response import success
from app.repositories.user_repository import UserRepository
from app.schemas.reservation_schema import ApprovalRequest, ReservationCreate, ReservationUpdate
from app.services.reservation_service import ReservationService

router = APIRouter(prefix="/api/reservations", tags=["试验预约"])

TeacherUser = Annotated[SysUser, Depends(require_roles("TEACHER", "ADMIN"))]
DirectorUser = Annotated[SysUser, Depends(require_roles("DIRECTOR", "ADMIN"))]


def _roles(db, user) -> list[str]:
    return UserRepository(db).get_role_codes(user.id)


@router.get("")
def list_reservations(
    db: DbSession,
    current_user: CurrentUser,
    status: Optional[str] = None,
    applicant_id: Optional[int] = Query(None, alias="applicantId"),
    teacher_id: Optional[int] = Query(None, alias="teacherId"),
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
):
    roles = _roles(db, current_user)
    result = ReservationService(db).list_reservations(
        current_user, roles, status, applicant_id, teacher_id, keyword, page, page_size
    )
    return success(result.model_dump(by_alias=True))


@router.get("/{reservation_id}")
def get_reservation(reservation_id: int, db: DbSession, current_user: CurrentUser):
    roles = _roles(db, current_user)
    result = ReservationService(db).get_detail(reservation_id, current_user, roles)
    return success(result.model_dump(by_alias=True))


@router.post("")
def create_reservation(payload: ReservationCreate, db: DbSession, current_user: CurrentUser):
    result = ReservationService(db).create_draft(payload, current_user)
    return success(result.model_dump(by_alias=True))


@router.put("/{reservation_id}")
def update_reservation(
    reservation_id: int,
    payload: ReservationUpdate,
    db: DbSession,
    current_user: CurrentUser,
):
    roles = _roles(db, current_user)
    result = ReservationService(db).update_draft(reservation_id, payload, current_user, roles)
    return success(result.model_dump(by_alias=True))


@router.post("/{reservation_id}/check-conflicts")
def check_conflicts(reservation_id: int, db: DbSession, current_user: CurrentUser):
    roles = _roles(db, current_user)
    result = ReservationService(db).check_conflicts(reservation_id, current_user, roles)
    return success(result.model_dump(by_alias=True))


@router.post("/{reservation_id}/submit")
def submit_reservation(reservation_id: int, db: DbSession, current_user: CurrentUser):
    roles = _roles(db, current_user)
    result = ReservationService(db).submit(reservation_id, current_user, roles)
    return success(result.model_dump(by_alias=True))


@router.post("/{reservation_id}/teacher-review")
def teacher_review(
    reservation_id: int,
    payload: ApprovalRequest,
    db: DbSession,
    current_user: TeacherUser,
):
    roles = _roles(db, current_user)
    result = ReservationService(db).teacher_review(reservation_id, payload, current_user, roles)
    return success(result.model_dump(by_alias=True))


@router.post("/{reservation_id}/director-approve")
def director_approve(
    reservation_id: int,
    payload: ApprovalRequest,
    db: DbSession,
    current_user: DirectorUser,
):
    roles = _roles(db, current_user)
    result = ReservationService(db).director_approve(reservation_id, payload, current_user, roles)
    return success(result.model_dump(by_alias=True))


@router.post("/{reservation_id}/cancel")
def cancel_reservation(reservation_id: int, db: DbSession, current_user: CurrentUser):
    roles = _roles(db, current_user)
    result = ReservationService(db).cancel(reservation_id, current_user, roles)
    return success(result.model_dump(by_alias=True))
