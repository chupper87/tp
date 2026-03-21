import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from employees.errors import EmailAlreadyInUse, EmployeeNotFound
from employees.schemas import EmployeeCreate, EmployeeUpdate
from idp.email_and_password.repo import get_user_by_email, hash_password
from log_setup import get_logger
from models import Employee, User

log = get_logger(__name__)

_EMPLOYEE_WITH_USER = selectinload(Employee.user)


async def _get_with_user(db: AsyncSession, employee_id: uuid.UUID) -> Employee | None:
    result = await db.execute(
        select(Employee).options(_EMPLOYEE_WITH_USER).where(Employee.id == employee_id)
    )
    return result.scalar_one_or_none()


async def get_employee_or_404(db: AsyncSession, employee_id: uuid.UUID) -> Employee:
    employee = await _get_with_user(db, employee_id)
    if employee is None:
        raise EmployeeNotFound(employee_id)
    return employee


async def list_employees(
    db: AsyncSession,
    *,
    is_active: bool | None = None,
    role: str | None = None,
) -> list[Employee]:
    q = select(Employee).options(_EMPLOYEE_WITH_USER)
    if is_active is not None:
        q = q.where(Employee.is_active == is_active)
    if role is not None:
        q = q.where(Employee.role == role)
    result = await db.execute(q.order_by(Employee.last_name, Employee.first_name))
    return list(result.scalars().all())


async def create_employee(db: AsyncSession, data: EmployeeCreate) -> Employee:
    if await get_user_by_email(db, data.email) is not None:
        raise EmailAlreadyInUse()

    user = User(
        email=data.email.lower(),
        hashed_password=hash_password(data.password),
        is_admin=False,
        is_active=True,
    )
    db.add(user)
    await db.flush()  # populate user.id before linking employee

    employee = Employee(
        user_id=user.id,
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        role=data.role,
        employment_type=data.employment_type,
        employment_degree=data.employment_degree,
        weekly_hours=data.weekly_hours,
        start_date=data.start_date,
        is_summer_worker=data.is_summer_worker,
        gender=data.gender,
        birth_date=data.birth_date,
        vacation_days=data.vacation_days,
    )
    db.add(employee)
    await db.commit()

    log.info("created_employee", employee_id=str(employee.id), email=data.email)
    return await get_employee_or_404(db, employee.id)


async def update_employee(
    db: AsyncSession,
    employee: Employee,
    data: EmployeeUpdate,
) -> Employee:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(employee, field, value)
    await db.commit()

    log.info("updated_employee", employee_id=str(employee.id))
    return await get_employee_or_404(db, employee.id)
