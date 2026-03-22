from datetime import date as date_type
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from absences import repo
from absences.schemas import AbsenceOut
from dependencies import get_current_employee, get_db
from models import Absence, Employee

router = APIRouter(prefix="/my", tags=["Absences (employee)"])


@router.get("/", response_model=list[AbsenceOut])
async def list_my_absences(
    absence_type: Optional[str] = None,
    date_from: Optional[date_type] = None,
    date_to: Optional[date_type] = None,
    db: AsyncSession = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
) -> list[Absence]:
    return await repo.list_absences(
        db,
        employee_id=employee.id,
        absence_type=absence_type,
        date_from=date_from,
        date_to=date_to,
    )
