import uuid
from datetime import date as date_type
from typing import Optional

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api_core import responses_from_api_errors
from care_visits import repo
from care_visits.errors import (
    CareVisitMustHaveEmployeeError,
    CareVisitNotFoundError,
    CustomerNotOnScheduleForVisitError,
    EmployeeAlreadyOnVisitError,
    EmployeeNotOnScheduleForVisitError,
    EmployeeNotOnVisitError,
    InvalidStatusTransitionError,
)
from care_visits.schemas import (
    AddEmployeeToVisit,
    CareVisitCreate,
    CareVisitDetailOut,
    CareVisitOut,
    CareVisitStatusUpdate,
    CareVisitUpdate,
)
from dependencies import get_authenticated_admin_user, get_db
from employees.errors import EmployeeNotFoundError
from models import CareVisit, User

router = APIRouter(tags=["Care Visits (admin)"])


@router.get("/", response_model=list[CareVisitOut])
async def list_care_visits(
    schedule_id: Optional[uuid.UUID] = None,
    customer_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = None,
    date_from: Optional[date_type] = None,
    date_to: Optional[date_type] = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> list[CareVisit]:
    return await repo.list_care_visits(
        db,
        schedule_id=schedule_id,
        customer_id=customer_id,
        status=status_filter,
        date_from=date_from,
        date_to=date_to,
    )


@router.post(
    "/",
    response_model=CareVisitDetailOut,
    status_code=status.HTTP_201_CREATED,
    responses=responses_from_api_errors(
        CustomerNotOnScheduleForVisitError,
        EmployeeNotOnScheduleForVisitError,
        EmployeeNotFoundError,
    ),
)
async def create_care_visit(
    data: CareVisitCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> CareVisit:
    return await repo.create_care_visit(db, data)


@router.get(
    "/{care_visit_id}",
    response_model=CareVisitDetailOut,
    responses=responses_from_api_errors(CareVisitNotFoundError),
)
async def get_care_visit(
    care_visit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> CareVisit:
    return await repo.get_care_visit_or_404(db, care_visit_id)


@router.patch(
    "/{care_visit_id}",
    response_model=CareVisitDetailOut,
    responses=responses_from_api_errors(CareVisitNotFoundError),
)
async def update_care_visit(
    care_visit_id: uuid.UUID,
    data: CareVisitUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> CareVisit:
    care_visit = await repo.get_care_visit_or_404(db, care_visit_id)
    return await repo.update_care_visit(db, care_visit, data)


@router.patch(
    "/{care_visit_id}/status",
    response_model=CareVisitDetailOut,
    responses=responses_from_api_errors(
        CareVisitNotFoundError, InvalidStatusTransitionError
    ),
)
async def update_care_visit_status(
    care_visit_id: uuid.UUID,
    data: CareVisitStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> CareVisit:
    care_visit = await repo.get_care_visit_or_404(db, care_visit_id)
    return await repo.update_status(db, care_visit, data)


@router.delete(
    "/{care_visit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=responses_from_api_errors(CareVisitNotFoundError),
)
async def delete_care_visit(
    care_visit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Response:
    care_visit = await repo.get_care_visit_or_404(db, care_visit_id)
    await repo.delete_care_visit(db, care_visit)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Employee assignment (double bemanning) ---


@router.post(
    "/{care_visit_id}/employees",
    response_model=CareVisitDetailOut,
    status_code=status.HTTP_201_CREATED,
    responses=responses_from_api_errors(
        CareVisitNotFoundError,
        EmployeeNotOnScheduleForVisitError,
        EmployeeAlreadyOnVisitError,
        EmployeeNotFoundError,
    ),
)
async def add_employee_to_visit(
    care_visit_id: uuid.UUID,
    data: AddEmployeeToVisit,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> CareVisit:
    care_visit = await repo.get_care_visit_or_404(db, care_visit_id)
    return await repo.add_employee(db, care_visit, data)


@router.delete(
    "/{care_visit_id}/employees/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=responses_from_api_errors(
        CareVisitNotFoundError,
        EmployeeNotOnVisitError,
        CareVisitMustHaveEmployeeError,
    ),
)
async def remove_employee_from_visit(
    care_visit_id: uuid.UUID,
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Response:
    care_visit = await repo.get_care_visit_or_404(db, care_visit_id)
    await repo.remove_employee(db, care_visit, employee_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
