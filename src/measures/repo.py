import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from log_setup import get_logger
from measures.errors import MeasureNameAlreadyInUse, MeasureNotFound
from measures.schemas import MeasureCreate, MeasureUpdate
from models import Measure

log = get_logger(__name__)


async def _get_by_name(db: AsyncSession, name: str) -> Measure | None:
    result = await db.execute(select(Measure).where(Measure.name == name))
    return result.scalar_one_or_none()


async def get_measure_or_404(db: AsyncSession, measure_id: uuid.UUID) -> Measure:
    result = await db.execute(select(Measure).where(Measure.id == measure_id))
    measure = result.scalar_one_or_none()
    if measure is None:
        raise MeasureNotFound(measure_id)
    return measure


async def list_measures(
    db: AsyncSession,
    *,
    is_active: bool | None = None,
    is_standard: bool | None = None,
    time_of_day: str | None = None,
) -> list[Measure]:
    q = select(Measure)
    if is_active is not None:
        q = q.where(Measure.is_active == is_active)
    if is_standard is not None:
        q = q.where(Measure.is_standard == is_standard)
    if time_of_day is not None:
        q = q.where(Measure.time_of_day == time_of_day)
    result = await db.execute(q.order_by(Measure.name))
    return list(result.scalars().all())


async def create_measure(db: AsyncSession, data: MeasureCreate) -> Measure:
    if await _get_by_name(db, data.name) is not None:
        raise MeasureNameAlreadyInUse(data.name)

    measure = Measure(
        name=data.name,
        default_duration=data.default_duration,
        description=data.description,
        time_of_day=data.time_of_day,
        time_flexibility=data.time_flexibility,
        is_standard=data.is_standard,
    )
    db.add(measure)
    await db.commit()

    log.info("created_measure", measure_id=str(measure.id), name=data.name)
    return await get_measure_or_404(db, measure.id)


async def update_measure(
    db: AsyncSession,
    measure: Measure,
    data: MeasureUpdate,
) -> Measure:
    update_data = data.model_dump(exclude_unset=True)

    if "name" in update_data:
        existing = await _get_by_name(db, update_data["name"])
        if existing is not None and existing.id != measure.id:
            raise MeasureNameAlreadyInUse(update_data["name"])

    for field, value in update_data.items():
        setattr(measure, field, value)
    await db.commit()

    log.info("updated_measure", measure_id=str(measure.id))
    return await get_measure_or_404(db, measure.id)
