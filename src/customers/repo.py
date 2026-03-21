import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from customers.errors import CustomerNotFound, KeyNumberAlreadyInUse
from customers.schemas import CustomerCreate, CustomerUpdate
from log_setup import get_logger
from models import Customer

log = get_logger(__name__)


async def _get_by_key_number(db: AsyncSession, key_number: int) -> Customer | None:
    result = await db.execute(select(Customer).where(Customer.key_number == key_number))
    return result.scalar_one_or_none()


async def get_customer_or_404(db: AsyncSession, customer_id: uuid.UUID) -> Customer:
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if customer is None:
        raise CustomerNotFound(customer_id)
    return customer


async def list_customers(
    db: AsyncSession,
    *,
    is_active: bool | None = None,
    care_level: str | None = None,
) -> list[Customer]:
    q = select(Customer)
    if is_active is not None:
        q = q.where(Customer.is_active == is_active)
    if care_level is not None:
        q = q.where(Customer.care_level == care_level)
    result = await db.execute(q.order_by(Customer.last_name, Customer.first_name))
    return list(result.scalars().all())


async def create_customer(db: AsyncSession, data: CustomerCreate) -> Customer:
    if await _get_by_key_number(db, data.key_number) is not None:
        raise KeyNumberAlreadyInUse(data.key_number)

    customer = Customer(
        first_name=data.first_name,
        last_name=data.last_name,
        key_number=data.key_number,
        address=data.address,
        care_level=data.care_level,
        gender=data.gender,
        approved_hours=data.approved_hours,
    )
    db.add(customer)
    await db.commit()

    log.info("created_customer", customer_id=str(customer.id))
    return await get_customer_or_404(db, customer.id)


async def update_customer(
    db: AsyncSession,
    customer: Customer,
    data: CustomerUpdate,
) -> Customer:
    update_data = data.model_dump(exclude_unset=True)

    if "key_number" in update_data:
        existing = await _get_by_key_number(db, update_data["key_number"])
        if existing is not None and existing.id != customer.id:
            raise KeyNumberAlreadyInUse(update_data["key_number"])

    for field, value in update_data.items():
        setattr(customer, field, value)
    await db.commit()

    log.info("updated_customer", customer_id=str(customer.id))
    return await get_customer_or_404(db, customer.id)
