import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api_core import responses_from_api_errors
from customers import repo
from customers.errors import CustomerNotFoundError, KeyNumberAlreadyInUseError
from customers.schemas import CustomerCreate, CustomerOut, CustomerUpdate
from dependencies import get_authenticated_admin_user, get_db
from models import Customer, User

router = APIRouter(tags=["Customers (admin)"])


@router.get("/", response_model=list[CustomerOut])
async def list_customers(
    is_active: bool | None = None,
    care_level: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> list[Customer]:
    return await repo.list_customers(db, is_active=is_active, care_level=care_level)


@router.post(
    "/",
    response_model=CustomerOut,
    status_code=status.HTTP_201_CREATED,
    responses=responses_from_api_errors(KeyNumberAlreadyInUseError),
)
async def create_customer(
    data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Customer:
    return await repo.create_customer(db, data)


@router.get(
    "/{customer_id}",
    response_model=CustomerOut,
    responses=responses_from_api_errors(CustomerNotFoundError),
)
async def get_customer(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Customer:
    return await repo.get_customer_or_404(db, customer_id)


@router.patch(
    "/{customer_id}",
    response_model=CustomerOut,
    responses=responses_from_api_errors(
        CustomerNotFoundError, KeyNumberAlreadyInUseError
    ),
)
async def update_customer(
    customer_id: uuid.UUID,
    data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Customer:
    customer = await repo.get_customer_or_404(db, customer_id)
    return await repo.update_customer(db, customer, data)
