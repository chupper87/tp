import uuid
from datetime import date as date_type
from typing import Optional

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from absences import repo
from absences.errors import (
    AbsenceInvalidDateRangeError,
    AbsenceNotFoundError,
    AbsenceOverlapError,
)
from absences.schemas import AbsenceCreate, AbsenceDetailOut, AbsenceOut, AbsenceUpdate
from api_core import responses_from_api_errors
from dependencies import get_authenticated_admin_user, get_db
from employees.errors import EmployeeNotFoundError
from models import Absence, User

router = APIRouter(tags=["Absences (admin)"])


@router.get("/", response_model=list[AbsenceOut])
async def list_absences(
    employee_id: Optional[uuid.UUID] = None,
    absence_type: Optional[str] = None,
    date_from: Optional[date_type] = None,
    date_to: Optional[date_type] = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> list[Absence]:
    return await repo.list_absences(
        db,
        employee_id=employee_id,
        absence_type=absence_type,
        date_from=date_from,
        date_to=date_to,
    )


@router.post(
    "/",
    response_model=AbsenceDetailOut,
    status_code=status.HTTP_201_CREATED,
    responses=responses_from_api_errors(
        EmployeeNotFoundError, AbsenceOverlapError, AbsenceInvalidDateRangeError
    ),
)
async def create_absence(
    data: AbsenceCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Absence:
    return await repo.create_absence(db, data)


@router.get(
    "/{absence_id}",
    response_model=AbsenceDetailOut,
    responses=responses_from_api_errors(AbsenceNotFoundError),
)
async def get_absence(
    absence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Absence:
    return await repo.get_absence_or_404(db, absence_id)


@router.patch(
    "/{absence_id}",
    response_model=AbsenceDetailOut,
    responses=responses_from_api_errors(
        AbsenceNotFoundError, AbsenceOverlapError, AbsenceInvalidDateRangeError
    ),
)
async def update_absence(
    absence_id: uuid.UUID,
    data: AbsenceUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Absence:
    absence = await repo.get_absence_or_404(db, absence_id)
    return await repo.update_absence(db, absence, data)


@router.delete(
    "/{absence_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=responses_from_api_errors(AbsenceNotFoundError),
)
async def delete_absence(
    absence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Response:
    absence = await repo.get_absence_or_404(db, absence_id)
    await repo.delete_absence(db, absence)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
