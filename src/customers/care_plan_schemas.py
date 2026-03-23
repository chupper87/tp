import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

Frequency = Literal["daily", "weekly", "biweekly", "monthly"]
TimeOfDay = Literal["morning", "midday", "afternoon", "evening", "night"]
TimeFlexibility = Literal["fixed", "flexible", "very_flexible"]
DayOfWeek = Literal[
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
]


class CustomerMeasureCreate(BaseModel):
    measure_id: uuid.UUID
    frequency: Frequency = "weekly"
    days_of_week: Optional[list[DayOfWeek]] = None
    occurrences_per_week: Optional[int] = None
    customer_duration: Optional[int] = None
    time_of_day: Optional[TimeOfDay] = None
    time_flexibility: Optional[TimeFlexibility] = None
    customer_notes: Optional[str] = None


class CustomerMeasureUpdate(BaseModel):
    frequency: Optional[Frequency] = None
    days_of_week: Optional[list[DayOfWeek]] = None
    occurrences_per_week: Optional[int] = None
    customer_duration: Optional[int] = None
    time_of_day: Optional[TimeOfDay] = None
    time_flexibility: Optional[TimeFlexibility] = None
    customer_notes: Optional[str] = None


class CustomerMeasureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    measure_id: uuid.UUID
    frequency: str
    days_of_week: Optional[list[str]]
    occurrences_per_week: Optional[int]
    customer_duration: Optional[int]
    customer_notes: Optional[str]
    time_of_day: Optional[str]
    time_flexibility: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Denormalized from the Measure relation
    measure_name: str
    measure_default_duration: int
