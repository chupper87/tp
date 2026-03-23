import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from customers.care_plan_schemas import CustomerMeasureCreate, CustomerMeasureUpdate
from customers.errors import (
    CustomerMeasureDuplicate,
    CustomerMeasureNotFound,
    CustomerNotFound,
)
from log_setup import get_logger
from measures.errors import MeasureNotFound
from models import Customer, CustomerMeasure, Measure

log = get_logger(__name__)


async def _get_customer(db: AsyncSession, customer_id: uuid.UUID) -> Customer:
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if customer is None:
        raise CustomerNotFound(customer_id)
    return customer


async def _get_measure(db: AsyncSession, measure_id: uuid.UUID) -> Measure:
    result = await db.execute(select(Measure).where(Measure.id == measure_id))
    measure = result.scalar_one_or_none()
    if measure is None:
        raise MeasureNotFound(measure_id)
    return measure


async def list_customer_measures(
    db: AsyncSession, customer_id: uuid.UUID
) -> list[CustomerMeasure]:
    await _get_customer(db, customer_id)
    result = await db.execute(
        select(CustomerMeasure)
        .where(CustomerMeasure.customer_id == customer_id)
        .options(selectinload(CustomerMeasure.measure))
        .order_by(CustomerMeasure.created_at)
    )
    return list(result.scalars().all())


async def get_customer_measure_or_404(
    db: AsyncSession, customer_measure_id: uuid.UUID
) -> CustomerMeasure:
    result = await db.execute(
        select(CustomerMeasure)
        .where(CustomerMeasure.id == customer_measure_id)
        .options(selectinload(CustomerMeasure.measure))
    )
    cm = result.scalar_one_or_none()
    if cm is None:
        raise CustomerMeasureNotFound(customer_measure_id)
    return cm


async def create_customer_measure(
    db: AsyncSession, customer_id: uuid.UUID, data: CustomerMeasureCreate
) -> CustomerMeasure:
    await _get_customer(db, customer_id)
    await _get_measure(db, data.measure_id)

    # Check uniqueness
    existing = await db.execute(
        select(CustomerMeasure).where(
            CustomerMeasure.customer_id == customer_id,
            CustomerMeasure.measure_id == data.measure_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise CustomerMeasureDuplicate(customer_id, data.measure_id)

    cm = CustomerMeasure(
        customer_id=customer_id,
        measure_id=data.measure_id,
        frequency=data.frequency,
        days_of_week=data.days_of_week,
        occurrences_per_week=data.occurrences_per_week,
        customer_duration=data.customer_duration,
        time_of_day=data.time_of_day,
        time_flexibility=data.time_flexibility,
        customer_notes=data.customer_notes,
    )
    db.add(cm)
    await db.commit()

    log.info(
        "created_customer_measure",
        customer_id=str(customer_id),
        measure_id=str(data.measure_id),
    )
    return await get_customer_measure_or_404(db, cm.id)


async def update_customer_measure(
    db: AsyncSession, cm: CustomerMeasure, data: CustomerMeasureUpdate
) -> CustomerMeasure:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cm, field, value)
    await db.commit()

    log.info("updated_customer_measure", customer_measure_id=str(cm.id))
    return await get_customer_measure_or_404(db, cm.id)


async def delete_customer_measure(db: AsyncSession, cm: CustomerMeasure) -> None:
    await db.delete(cm)
    await db.commit()
    log.info("deleted_customer_measure", customer_measure_id=str(cm.id))
