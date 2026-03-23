import uuid
from datetime import date as date_type
from typing import Optional

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api_core import responses_from_api_errors
from audit.repo import audit_log
from customers.errors import CustomerNotFoundError
from dependencies import get_authenticated_admin_user, get_db
from employees.errors import EmployeeNotFoundError
from measures.errors import MeasureNotFoundError
from models import (
    Schedule,
    ScheduleCustomer,
    ScheduleEmployee,
    ScheduleMeasure,
    User,
)
from schedules import planning, repo
from schedules.errors import (
    CustomerAlreadyOnScheduleError,
    CustomerNotOnScheduleError,
    CustomerNotOnScheduleForMeasureError,
    EmployeeAbsenceConflictError,
    EmployeeAlreadyOnScheduleError,
    EmployeeNotOnScheduleError,
    MeasureAlreadyOnScheduleError,
    ScheduleConflictError,
    ScheduleMeasureNotFoundError,
    ScheduleNotFoundError,
)
from schedules.planning_schemas import (
    ContinuityPreviewOut,
    ScheduleFulfillmentOut,
    ScheduleUtilizationOut,
)
from schedules.schemas import (
    AssignCustomerRequest,
    AssignEmployeeRequest,
    ScheduleCreate,
    ScheduleCustomerOut,
    ScheduleDetailOut,
    ScheduleEmployeeOut,
    ScheduleMeasureCreate,
    ScheduleMeasureOut,
    ScheduleMeasureUpdate,
    ScheduleOut,
    ScheduleUpdate,
)

router = APIRouter(tags=["Schedules (admin)"])


@router.get("/", response_model=list[ScheduleOut])
async def list_schedules(
    date_from: Optional[date_type] = None,
    date_to: Optional[date_type] = None,
    shift_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> list[Schedule]:
    return await repo.list_schedules(
        db, date_from=date_from, date_to=date_to, shift_type=shift_type
    )


@router.post(
    "/",
    response_model=ScheduleDetailOut,
    status_code=status.HTTP_201_CREATED,
    responses=responses_from_api_errors(ScheduleConflictError),
)
async def create_schedule(
    data: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_authenticated_admin_user),
) -> Schedule:
    schedule = await repo.create_schedule(db, data)
    await audit_log(
        db,
        user_id=admin.id,
        action="created",
        resource_type="schedule",
        resource_id=schedule.id,
    )
    return schedule


@router.get(
    "/{schedule_id}",
    response_model=ScheduleDetailOut,
    responses=responses_from_api_errors(ScheduleNotFoundError),
)
async def get_schedule(
    schedule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Schedule:
    return await repo.get_schedule_or_404(db, schedule_id)


@router.patch(
    "/{schedule_id}",
    response_model=ScheduleDetailOut,
    responses=responses_from_api_errors(ScheduleNotFoundError, ScheduleConflictError),
)
async def update_schedule(
    schedule_id: uuid.UUID,
    data: ScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_authenticated_admin_user),
) -> Schedule:
    schedule = await repo.get_schedule_or_404(db, schedule_id)
    changes = data.model_dump(exclude_unset=True)
    result = await repo.update_schedule(db, schedule, data)
    await audit_log(
        db,
        user_id=admin.id,
        action="updated",
        resource_type="schedule",
        resource_id=schedule_id,
        changes=changes,
    )
    return result


# --- Employees ---


@router.post(
    "/{schedule_id}/employees",
    response_model=ScheduleEmployeeOut,
    status_code=status.HTTP_201_CREATED,
    responses=responses_from_api_errors(
        ScheduleNotFoundError,
        EmployeeNotFoundError,
        EmployeeAlreadyOnScheduleError,
        EmployeeAbsenceConflictError,
    ),
)
async def assign_employee(
    schedule_id: uuid.UUID,
    data: AssignEmployeeRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> ScheduleEmployee:
    schedule = await repo.get_schedule_or_404(db, schedule_id)
    return await repo.assign_employee(db, schedule, data.employee_id)


@router.delete(
    "/{schedule_id}/employees/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=responses_from_api_errors(
        ScheduleNotFoundError, EmployeeNotOnScheduleError
    ),
)
async def remove_employee(
    schedule_id: uuid.UUID,
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Response:
    schedule = await repo.get_schedule_or_404(db, schedule_id)
    await repo.remove_employee(db, schedule, employee_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Customers ---


@router.post(
    "/{schedule_id}/customers",
    response_model=ScheduleCustomerOut,
    status_code=status.HTTP_201_CREATED,
    responses=responses_from_api_errors(
        ScheduleNotFoundError, CustomerNotFoundError, CustomerAlreadyOnScheduleError
    ),
)
async def assign_customer(
    schedule_id: uuid.UUID,
    data: AssignCustomerRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> ScheduleCustomer:
    schedule = await repo.get_schedule_or_404(db, schedule_id)
    return await repo.assign_customer(db, schedule, data.customer_id)


@router.delete(
    "/{schedule_id}/customers/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=responses_from_api_errors(
        ScheduleNotFoundError, CustomerNotOnScheduleError
    ),
)
async def remove_customer(
    schedule_id: uuid.UUID,
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Response:
    schedule = await repo.get_schedule_or_404(db, schedule_id)
    await repo.remove_customer(db, schedule, customer_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Planned measures ---


@router.post(
    "/{schedule_id}/measures",
    response_model=ScheduleMeasureOut,
    status_code=status.HTTP_201_CREATED,
    responses=responses_from_api_errors(
        ScheduleNotFoundError,
        CustomerNotOnScheduleForMeasureError,
        MeasureNotFoundError,
        MeasureAlreadyOnScheduleError,
    ),
)
async def add_measure(
    schedule_id: uuid.UUID,
    data: ScheduleMeasureCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> ScheduleMeasure:
    schedule = await repo.get_schedule_or_404(db, schedule_id)
    return await repo.add_measure(db, schedule, data)


@router.patch(
    "/{schedule_id}/measures/{schedule_measure_id}",
    response_model=ScheduleMeasureOut,
    responses=responses_from_api_errors(
        ScheduleNotFoundError, ScheduleMeasureNotFoundError
    ),
)
async def update_measure(
    schedule_id: uuid.UUID,
    schedule_measure_id: uuid.UUID,
    data: ScheduleMeasureUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> ScheduleMeasure:
    await repo.get_schedule_or_404(db, schedule_id)
    sm = await repo.get_schedule_measure_or_404(db, schedule_measure_id)
    return await repo.update_measure(db, sm, data)


@router.delete(
    "/{schedule_id}/measures/{schedule_measure_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=responses_from_api_errors(
        ScheduleNotFoundError, ScheduleMeasureNotFoundError
    ),
)
async def remove_measure(
    schedule_id: uuid.UUID,
    schedule_measure_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Response:
    await repo.get_schedule_or_404(db, schedule_id)
    sm = await repo.get_schedule_measure_or_404(db, schedule_measure_id)
    await repo.remove_measure(db, sm)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Planning intelligence ---


@router.get(
    "/{schedule_id}/fulfillment",
    response_model=ScheduleFulfillmentOut,
    responses=responses_from_api_errors(ScheduleNotFoundError),
)
async def get_fulfillment(
    schedule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> dict:
    schedule = await repo.get_schedule_or_404(db, schedule_id)
    return await planning.compute_fulfillment(db, schedule)


@router.get(
    "/{schedule_id}/utilization",
    response_model=ScheduleUtilizationOut,
    responses=responses_from_api_errors(ScheduleNotFoundError),
)
async def get_utilization(
    schedule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> dict:
    schedule = await repo.get_schedule_or_404(db, schedule_id)
    return await planning.compute_utilization(db, schedule)


@router.get(
    "/{schedule_id}/continuity-preview",
    response_model=ContinuityPreviewOut,
    responses=responses_from_api_errors(ScheduleNotFoundError),
)
async def get_continuity_preview(
    schedule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> dict:
    schedule = await repo.get_schedule_or_404(db, schedule_id)
    return await planning.compute_continuity_preview(db, schedule)
