import uuid
from datetime import time as time_type
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


# --- Employee Timeline ---


class TimelineMeasureOut(BaseModel):
    schedule_measure_id: uuid.UUID
    measure_id: uuid.UUID
    measure_name: str
    duration: int


class TimelineVisitOut(BaseModel):
    care_visit_id: uuid.UUID
    customer_id: uuid.UUID
    customer_name: str
    planned_start_time: time_type
    planned_end_time: time_type
    duration: int
    status: str
    measures: list[TimelineMeasureOut]


class EmployeeTimelineOut(BaseModel):
    employee_id: uuid.UUID
    employee_name: str
    total_visit_minutes: int
    total_gap_minutes: int
    visits: list[TimelineVisitOut]


class ScheduleTimelineOut(BaseModel):
    schedule_id: uuid.UUID
    shift_type: Optional[str]
    shift_start: time_type
    shift_end: time_type
    employees: list[EmployeeTimelineOut]
    unassigned_measures_count: int


# --- Customer Schedule ---


class CustomerVisitMeasureOut(BaseModel):
    measure_name: str
    duration: int


class CustomerVisitOut(BaseModel):
    care_visit_id: uuid.UUID
    planned_start_time: time_type
    planned_end_time: time_type
    duration: int
    employee_names: list[str]
    measures: list[CustomerVisitMeasureOut]


class CustomerDayOut(BaseModel):
    customer_id: uuid.UUID
    customer_name: str
    care_level: Optional[str]
    approved_hours_monthly: Optional[float]
    total_planned_minutes_today: int
    visits: list[CustomerVisitOut]
    warnings: list[str]


class CustomerScheduleOut(BaseModel):
    schedule_id: uuid.UUID
    customers: list[CustomerDayOut]
