import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

TimeOfDay = Literal["morning", "midday", "afternoon", "evening"]
TimeFlexibility = Literal["fixed", "flexible", "very_flexible"]


class MeasureCreate(BaseModel):
    name: str
    default_duration: int
    description: Optional[str] = None
    time_of_day: Optional[TimeOfDay] = None
    time_flexibility: Optional[TimeFlexibility] = None
    is_standard: bool = False


class MeasureUpdate(BaseModel):
    name: Optional[str] = None
    default_duration: Optional[int] = None
    description: Optional[str] = None
    time_of_day: Optional[TimeOfDay] = None
    time_flexibility: Optional[TimeFlexibility] = None
    is_standard: Optional[bool] = None
    is_active: Optional[bool] = None


class MeasureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    default_duration: int
    description: Optional[str]
    time_of_day: Optional[str]
    time_flexibility: Optional[str]
    is_standard: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
