import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api_core import responses_from_api_errors
from audit.repo import audit_log
from customers import care_plan_repo as repo
from customers.care_plan_schemas import (
    CustomerMeasureCreate,
    CustomerMeasureOut,
    CustomerMeasureUpdate,
)
from customers.errors import (
    CustomerMeasureDuplicateError,
    CustomerMeasureNotFoundError,
    CustomerNotFoundError,
)
from dependencies import get_authenticated_admin_user, get_db
from measures.errors import MeasureNotFoundError
from models import User

router = APIRouter(tags=["Customer Care Plans (admin)"])


def _to_out(cm) -> dict:
    """Build CustomerMeasureOut-compatible dict with denormalized measure fields."""
    return {
        "id": cm.id,
        "customer_id": cm.customer_id,
        "measure_id": cm.measure_id,
        "frequency": cm.frequency,
        "days_of_week": cm.days_of_week,
        "occurrences_per_week": cm.occurrences_per_week,
        "customer_duration": cm.customer_duration,
        "customer_notes": cm.customer_notes,
        "time_of_day": cm.time_of_day,
        "time_flexibility": cm.time_flexibility,
        "created_at": cm.created_at,
        "updated_at": cm.updated_at,
        "measure_name": cm.measure.name,
        "measure_default_duration": cm.measure.default_duration,
    }


@router.get(
    "/{customer_id}/measures",
    response_model=list[CustomerMeasureOut],
    responses=responses_from_api_errors(CustomerNotFoundError),
)
async def list_customer_measures(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> list[dict]:
    measures = await repo.list_customer_measures(db, customer_id)
    return [_to_out(cm) for cm in measures]


@router.post(
    "/{customer_id}/measures",
    response_model=CustomerMeasureOut,
    status_code=status.HTTP_201_CREATED,
    responses=responses_from_api_errors(
        CustomerNotFoundError, MeasureNotFoundError, CustomerMeasureDuplicateError
    ),
)
async def create_customer_measure(
    customer_id: uuid.UUID,
    data: CustomerMeasureCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_authenticated_admin_user),
) -> dict:
    cm = await repo.create_customer_measure(db, customer_id, data)
    await audit_log(
        db,
        user_id=admin.id,
        action="created",
        resource_type="customer_measure",
        resource_id=cm.id,
    )
    return _to_out(cm)


@router.patch(
    "/{customer_id}/measures/{customer_measure_id}",
    response_model=CustomerMeasureOut,
    responses=responses_from_api_errors(
        CustomerNotFoundError, CustomerMeasureNotFoundError
    ),
)
async def update_customer_measure(
    customer_id: uuid.UUID,
    customer_measure_id: uuid.UUID,
    data: CustomerMeasureUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_authenticated_admin_user),
) -> dict:
    cm = await repo.get_customer_measure_or_404(db, customer_measure_id)
    changes = data.model_dump(exclude_unset=True)
    result = await repo.update_customer_measure(db, cm, data)
    await audit_log(
        db,
        user_id=admin.id,
        action="updated",
        resource_type="customer_measure",
        resource_id=customer_measure_id,
        changes=changes,
    )
    return _to_out(result)


@router.delete(
    "/{customer_id}/measures/{customer_measure_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=responses_from_api_errors(
        CustomerNotFoundError, CustomerMeasureNotFoundError
    ),
)
async def delete_customer_measure(
    customer_id: uuid.UUID,
    customer_measure_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_authenticated_admin_user),
) -> Response:
    cm = await repo.get_customer_measure_or_404(db, customer_measure_id)
    await repo.delete_customer_measure(db, cm)
    await audit_log(
        db,
        user_id=admin.id,
        action="deleted",
        resource_type="customer_measure",
        resource_id=customer_measure_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
