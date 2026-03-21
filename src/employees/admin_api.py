import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api_core import responses_from_api_errors
from dependencies import get_authenticated_admin_user, get_db
from employees import repo
from employees.errors import EmailAlreadyInUseError, EmployeeNotFoundError
from employees.schemas import EmployeeCreate, EmployeeOut, EmployeeUpdate
from models import Employee, User

router = APIRouter(tags=["Employees (admin)"])


@router.get("/", response_model=list[EmployeeOut])
async def list_employees(
    is_active: bool | None = None,
    role: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> list[Employee]:
    return await repo.list_employees(db, is_active=is_active, role=role)


@router.post(
    "/",
    response_model=EmployeeOut,
    status_code=status.HTTP_201_CREATED,
    responses=responses_from_api_errors(EmailAlreadyInUseError),
)
async def create_employee(
    data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Employee:
    return await repo.create_employee(db, data)


@router.get(
    "/{employee_id}",
    response_model=EmployeeOut,
    responses=responses_from_api_errors(EmployeeNotFoundError),
)
async def get_employee(
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Employee:
    return await repo.get_employee_or_404(db, employee_id)


@router.patch(
    "/{employee_id}",
    response_model=EmployeeOut,
    responses=responses_from_api_errors(EmployeeNotFoundError),
)
async def update_employee(
    employee_id: uuid.UUID,
    data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Employee:
    employee = await repo.get_employee_or_404(db, employee_id)
    return await repo.update_employee(db, employee, data)
