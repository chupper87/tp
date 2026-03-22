import uuid
from datetime import date as date_type
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

VisitStatusType = Literal[
    "planned",
    "completed",
    "canceled",
    "no_show",
    "partially_completed",
    "rescheduled",
]


class EmployeeOnVisitCreate(BaseModel):
    employee_id: uuid.UUID
    is_primary: bool = False
    notes: Optional[str] = None


class CareVisitCreate(BaseModel):
    schedule_id: uuid.UUID
    customer_id: uuid.UUID
    duration: int = Field(gt=0)
    notes: Optional[str] = None
    employees: list[EmployeeOnVisitCreate] = Field(min_length=1)


class CareVisitUpdate(BaseModel):
    duration: Optional[int] = Field(default=None, gt=0)
    notes: Optional[str] = None


class CareVisitStatusUpdate(BaseModel):
    status: VisitStatusType


class AddEmployeeToVisit(BaseModel):
    employee_id: uuid.UUID
    is_primary: bool = False
    notes: Optional[str] = None


# --- Response schemas ---


class _EmployeeBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str


class _CustomerBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str


class EmployeeCareVisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: uuid.UUID
    is_primary: bool
    notes: Optional[str]
    employee: _EmployeeBrief


class CareVisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    date: date_type
    status: str
    duration: int
    notes: Optional[str]
    schedule_id: uuid.UUID
    customer_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class CareVisitDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    date: date_type
    status: str
    duration: int
    notes: Optional[str]
    schedule_id: uuid.UUID
    customer_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    employees: list[EmployeeCareVisitOut]
    customer: _CustomerBrief
