import uuid
from datetime import date as date_type
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, model_validator

ShiftType = Literal["morning", "day", "evening", "night"]
TimeOfDay = Literal["morning", "midday", "afternoon", "evening", "night"]


class ScheduleCreate(BaseModel):
    date: date_type
    shift_type: Optional[ShiftType] = None
    custom_shift: Optional[str] = None

    @model_validator(mode="after")
    def check_shift_provided(self) -> "ScheduleCreate":
        if self.shift_type is None and self.custom_shift is None:
            raise ValueError("Either shift_type or custom_shift must be provided")
        return self


class ScheduleUpdate(BaseModel):
    date: Optional[date_type] = None
    shift_type: Optional[ShiftType] = None
    custom_shift: Optional[str] = None


class ScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    date: date_type
    shift_type: Optional[str]
    custom_shift: Optional[str]
    created_at: datetime
    updated_at: datetime


# --- Sub-resource request schemas ---


class AssignEmployeeRequest(BaseModel):
    employee_id: uuid.UUID


class AssignCustomerRequest(BaseModel):
    customer_id: uuid.UUID


class ScheduleMeasureCreate(BaseModel):
    customer_id: uuid.UUID
    measure_id: uuid.UUID
    time_of_day: Optional[TimeOfDay] = None
    custom_duration: Optional[int] = None
    notes: Optional[str] = None


class ScheduleMeasureUpdate(BaseModel):
    time_of_day: Optional[TimeOfDay] = None
    custom_duration: Optional[int] = None
    notes: Optional[str] = None


# --- Sub-resource response schemas ---


class ScheduleMeasureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    schedule_id: uuid.UUID
    customer_id: uuid.UUID
    measure_id: uuid.UUID
    time_of_day: Optional[str]
    custom_duration: Optional[int]
    notes: Optional[str]
    created_at: datetime


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


class ScheduleEmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: uuid.UUID
    employee: _EmployeeBrief


class ScheduleCustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: uuid.UUID
    customer: _CustomerBrief


class ScheduleDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    date: date_type
    shift_type: Optional[str]
    custom_shift: Optional[str]
    created_at: datetime
    updated_at: datetime
    employees: list[ScheduleEmployeeOut]
    customers: list[ScheduleCustomerOut]
    measures: list[ScheduleMeasureOut]
