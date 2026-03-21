import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

CareLevel = Literal["high", "medium", "low"]


class CustomerCreate(BaseModel):
    first_name: str
    last_name: str
    key_number: int
    address: str
    care_level: Optional[CareLevel] = None
    gender: Optional[str] = None
    approved_hours: Optional[float] = None


class CustomerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    key_number: Optional[int] = None
    address: Optional[str] = None
    care_level: Optional[CareLevel] = None
    gender: Optional[str] = None
    approved_hours: Optional[float] = None
    is_active: Optional[bool] = None


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    key_number: int
    address: str
    care_level: Optional[str]
    gender: Optional[str]
    approved_hours: Optional[float]
    is_active: bool
    created_at: datetime
    updated_at: datetime
