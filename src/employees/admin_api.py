import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api_core import responses_from_api_errors
from audit.repo import audit_log
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
    admin: User = Depends(get_authenticated_admin_user),
) -> Employee:
    employee = await repo.create_employee(db, data)
    await audit_log(
        db,
        user_id=admin.id,
        action="created",
        resource_type="employee",
        resource_id=employee.id,
    )
    return employee


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
    admin: User = Depends(get_authenticated_admin_user),
) -> Employee:
    employee = await repo.get_employee_or_404(db, employee_id)
    changes = data.model_dump(exclude_unset=True)
    result = await repo.update_employee(db, employee, data)
    await audit_log(
        db,
        user_id=admin.id,
        action="updated",
        resource_type="employee",
        resource_id=employee_id,
        changes=changes,
    )
    return result
