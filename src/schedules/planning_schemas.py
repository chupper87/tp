import uuid
from typing import Optional

from pydantic import BaseModel


# --- Fulfillment ---


class RequiredMeasureOut(BaseModel):
    customer_measure_id: uuid.UUID
    measure_id: uuid.UUID
    measure_name: str
    frequency: str
    time_of_day: Optional[str]
    expected_duration: int
    is_required: bool
    is_fulfilled: bool
    schedule_measure_id: Optional[uuid.UUID]


class CustomerFulfillmentOut(BaseModel):
    customer_id: uuid.UUID
    customer_name: str
    care_level: Optional[str]
    required_measures: list[RequiredMeasureOut]
    total_required: int
    total_fulfilled: int
    total_duration_minutes: int


class ScheduleFulfillmentOut(BaseModel):
    schedule_id: uuid.UUID
    customers: list[CustomerFulfillmentOut]


# --- Utilization ---


class ScheduleUtilizationOut(BaseModel):
    schedule_id: uuid.UUID
    shift_type: Optional[str]
    total_planned_minutes: int
    total_capacity_minutes: int
    employee_count: int
    utilization_pct: float
    per_employee_avg_minutes: int
    per_employee_capacity_minutes: int


# --- Continuity Preview ---


class EmployeeCustomerFamiliarityOut(BaseModel):
    employee_id: uuid.UUID
    employee_name: str
    customer_id: uuid.UUID
    customer_name: str
    shared_schedules_last_60_days: int
    familiarity_score: float


class ContinuityPreviewOut(BaseModel):
    schedule_id: uuid.UUID
    average_familiarity: float
    entries: list[EmployeeCustomerFamiliarityOut]
