import uuid
from datetime import date as date_type

from pydantic import BaseModel, ConfigDict


class EmployeeHoursRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: uuid.UUID
    first_name: str
    last_name: str
    total_minutes: int
    visit_count: int


class EmployeeHoursReport(BaseModel):
    date_from: date_type
    date_to: date_type
    rows: list[EmployeeHoursRow]


class CustomerHoursRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: uuid.UUID
    first_name: str
    last_name: str
    total_minutes: int
    visit_count: int


class CustomerHoursReport(BaseModel):
    date_from: date_type
    date_to: date_type
    rows: list[CustomerHoursRow]


class VisitStatusCount(BaseModel):
    status: str
    count: int


class VisitSummaryReport(BaseModel):
    date_from: date_type
    date_to: date_type
    total: int
    by_status: list[VisitStatusCount]


class ContinuityRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: uuid.UUID
    first_name: str
    last_name: str
    total_visits: int
    unique_employees: int
    continuity_score: float


class ContinuityReport(BaseModel):
    date_from: date_type
    date_to: date_type
    average_score: float
    rows: list[ContinuityRow]


class FlexHoursRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: uuid.UUID
    first_name: str
    last_name: str
    worked_minutes: int
    contracted_minutes: int | None
    flex_minutes: int | None


class FlexHoursReport(BaseModel):
    date_from: date_type
    date_to: date_type
    rows: list[FlexHoursRow]
