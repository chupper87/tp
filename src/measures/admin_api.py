import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api_core import responses_from_api_errors
from dependencies import get_authenticated_admin_user, get_db
from measures import repo
from measures.errors import MeasureNameAlreadyInUseError, MeasureNotFoundError
from measures.schemas import MeasureCreate, MeasureOut, MeasureUpdate
from models import Measure, User

router = APIRouter(tags=["Measures (admin)"])


@router.get("/", response_model=list[MeasureOut])
async def list_measures(
    is_active: bool | None = None,
    is_standard: bool | None = None,
    time_of_day: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> list[Measure]:
    return await repo.list_measures(
        db, is_active=is_active, is_standard=is_standard, time_of_day=time_of_day
    )


@router.post(
    "/",
    response_model=MeasureOut,
    status_code=status.HTTP_201_CREATED,
    responses=responses_from_api_errors(MeasureNameAlreadyInUseError),
)
async def create_measure(
    data: MeasureCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Measure:
    return await repo.create_measure(db, data)


@router.get(
    "/{measure_id}",
    response_model=MeasureOut,
    responses=responses_from_api_errors(MeasureNotFoundError),
)
async def get_measure(
    measure_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Measure:
    return await repo.get_measure_or_404(db, measure_id)


@router.patch(
    "/{measure_id}",
    response_model=MeasureOut,
    responses=responses_from_api_errors(
        MeasureNotFoundError, MeasureNameAlreadyInUseError
    ),
)
async def update_measure(
    measure_id: uuid.UUID,
    data: MeasureUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_authenticated_admin_user),
) -> Measure:
    measure = await repo.get_measure_or_404(db, measure_id)
    return await repo.update_measure(db, measure, data)
