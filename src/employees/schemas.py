import uuid
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr

RoleType = Literal["admin", "employee", "assistant_nurse", "care_assistant"]
EmploymentType = Literal["full_time", "part_time", "on_call", "temporary"]


class EmployeeUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str


class EmployeeCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: Optional[RoleType] = None
    employment_type: Optional[EmploymentType] = None
    employment_degree: Optional[int] = None
    weekly_hours: Optional[float] = None
    start_date: Optional[date] = None
    is_summer_worker: bool = False
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    vacation_days: Optional[int] = None


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[RoleType] = None
    employment_type: Optional[EmploymentType] = None
    employment_degree: Optional[int] = None
    weekly_hours: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    is_summer_worker: Optional[bool] = None
    vacation_days: Optional[int] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user: EmployeeUserOut
    first_name: str
    last_name: str
    phone: Optional[str]
    role: Optional[str]
    employment_type: Optional[str]
    employment_degree: Optional[int]
    weekly_hours: Optional[float]
    is_active: bool
    is_summer_worker: bool
    start_date: Optional[date]
    end_date: Optional[date]
    vacation_days: Optional[int]
    gender: Optional[str]
    birth_date: Optional[date]
    created_at: datetime
    updated_at: datetime
