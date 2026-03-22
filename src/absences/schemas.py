import uuid
from datetime import date as date_type
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

AbsenceTypeField = Literal[
    "sick", "vab", "vacation", "parental_leave", "leave_of_absence"
]


class AbsenceCreate(BaseModel):
    employee_id: uuid.UUID
    absence_type: AbsenceTypeField
    start_date: date_type
    end_date: date_type
    hours: Optional[float] = None
    notes: Optional[str] = None


class AbsenceUpdate(BaseModel):
    absence_type: Optional[AbsenceTypeField] = None
    start_date: Optional[date_type] = None
    end_date: Optional[date_type] = None
    hours: Optional[float] = None
    notes: Optional[str] = None


class _EmployeeBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str


class AbsenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    absence_type: str
    start_date: date_type
    end_date: date_type
    hours: Optional[float]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class AbsenceDetailOut(AbsenceOut):
    employee: _EmployeeBrief
