import uuid
from datetime import date as date_type
from datetime import datetime
from enum import StrEnum
from typing import Literal, Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer
from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(AsyncAttrs, DeclarativeBase):
    pass


def primary_key():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


# ---------------------------------------------------------------------------
# Enums (StrEnum for Python type safety, stored as String in DB)
# ---------------------------------------------------------------------------


class RoleType(StrEnum):
    ADMIN = "admin"
    EMPLOYEE = "employee"
    ASSISTANT_NURSE = "assistant_nurse"
    CARE_ASSISTANT = "care_assistant"


class EmploymentType(StrEnum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    ON_CALL = "on_call"
    TEMPORARY = "temporary"


class ShiftType(StrEnum):
    MORNING = "morning"
    DAY = "day"
    EVENING = "evening"
    NIGHT = "night"


class CareLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class VisitStatus(StrEnum):
    PLANNED = "planned"
    COMPLETED = "completed"
    CANCELED = "canceled"
    NO_SHOW = "no_show"
    PARTIALLY_COMPLETED = "partially_completed"
    RESCHEDULED = "rescheduled"


class AbsenceType(StrEnum):
    SICK = "sick"
    VAB = "vab"
    VACATION = "vacation"
    PARENTAL_LEAVE = "parental_leave"
    LEAVE_OF_ABSENCE = "leave_of_absence"


class Frequency(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


class TimeOfDay(StrEnum):
    MORNING = "morning"
    MIDDAY = "midday"
    AFTERNOON = "afternoon"
    EVENING = "evening"


class TimeFlexibility(StrEnum):
    FIXED = "fixed"
    FLEXIBLE = "flexible"
    VERY_FLEXIBLE = "very_flexible"


# ---------------------------------------------------------------------------
# Users & Auth
# ---------------------------------------------------------------------------


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = primary_key()
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    employee: Mapped[Optional["Employee"]] = relationship(
        "Employee", back_populates="user", uselist=False
    )


# ---------------------------------------------------------------------------
# Employees
# ---------------------------------------------------------------------------


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = primary_key()
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    birth_date: Mapped[Optional[date_type]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[
        Optional[Literal["admin", "employee", "assistant_nurse", "care_assistant"]]
    ] = mapped_column(String, nullable=True)
    employment_type: Mapped[
        Optional[Literal["full_time", "part_time", "on_call", "temporary"]]
    ] = mapped_column(String, nullable=True)
    employment_degree: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weekly_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vacation_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_summer_worker: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    start_date: Mapped[Optional[date_type]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date_type]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="employee")
    schedules: Mapped[list["ScheduleEmployee"]] = relationship(back_populates="employee")
    care_visits: Mapped[list["EmployeeCareVisit"]] = relationship(
        back_populates="employee"
    )
    absences: Mapped[list["Absence"]] = relationship(back_populates="employee")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class EmployeeCareVisit(Base):
    __tablename__ = "employee_care_visit"

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), primary_key=True
    )
    care_visit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("care_visits.id"), primary_key=True
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    employee: Mapped["Employee"] = relationship(back_populates="care_visits")
    care_visit: Mapped["CareVisit"] = relationship(back_populates="employees")


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = primary_key()
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    care_level: Mapped[Optional[Literal["high", "medium", "low"]]] = mapped_column(
        String, nullable=True
    )
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    approved_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    schedules: Mapped[list["ScheduleCustomer"]] = relationship(back_populates="customer")
    care_visits: Mapped[list["CareVisit"]] = relationship(back_populates="customer")
    measures: Mapped[list["CustomerMeasure"]] = relationship(back_populates="customer")


class CustomerMeasure(Base):
    __tablename__ = "customer_measures"

    id: Mapped[uuid.UUID] = primary_key()
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False
    )
    measure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("measures.id"), nullable=False
    )
    frequency: Mapped[Literal["daily", "weekly", "biweekly", "monthly"]] = mapped_column(
        String, nullable=False, default="weekly"
    )
    days_of_week: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    occurrences_per_week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    customer_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    customer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_of_day: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    time_flexibility: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("customer_id", "measure_id", name="uq__customer_measure"),
    )

    customer: Mapped["Customer"] = relationship("Customer", back_populates="measures")
    measure: Mapped["Measure"] = relationship("Measure", back_populates="customers")


# ---------------------------------------------------------------------------
# Measures
# ---------------------------------------------------------------------------


class Measure(Base):
    __tablename__ = "measures"

    id: Mapped[uuid.UUID] = primary_key()
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    default_duration: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_of_day: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    time_flexibility: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_standard: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_measure_time_of_day", "time_of_day"),
        Index("ix_measure_is_active", "is_active"),
        Index("ix_measure_active_time", "is_active", "time_of_day"),
    )

    care_visits: Mapped[list["MeasureCareVisit"]] = relationship(
        back_populates="measure"
    )
    schedules: Mapped[list["ScheduleMeasure"]] = relationship(back_populates="measure")
    customers: Mapped[list["CustomerMeasure"]] = relationship(back_populates="measure")


class MeasureCareVisit(Base):
    __tablename__ = "measure_care_visit"

    measure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("measures.id"), primary_key=True
    )
    care_visit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("care_visits.id"), primary_key=True
    )

    measure: Mapped["Measure"] = relationship(back_populates="care_visits")
    care_visit: Mapped["CareVisit"] = relationship(back_populates="measures")


# ---------------------------------------------------------------------------
# Schedules
# ---------------------------------------------------------------------------


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[uuid.UUID] = primary_key()
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    shift_type: Mapped[Optional[Literal["morning", "day", "evening", "night"]]] = (
        mapped_column(String, nullable=True)
    )
    custom_shift: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_schedule_date", "date"),)

    employees: Mapped[list["ScheduleEmployee"]] = relationship(back_populates="schedule")
    customers: Mapped[list["ScheduleCustomer"]] = relationship(back_populates="schedule")
    measures: Mapped[list["ScheduleMeasure"]] = relationship(back_populates="schedule")
    care_visits: Mapped[list["CareVisit"]] = relationship(back_populates="schedule")


class ScheduleEmployee(Base):
    __tablename__ = "schedule_employee"

    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schedules.id"), primary_key=True
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), primary_key=True
    )

    schedule: Mapped["Schedule"] = relationship(back_populates="employees")
    employee: Mapped["Employee"] = relationship(back_populates="schedules")


class ScheduleCustomer(Base):
    __tablename__ = "schedule_customer"

    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schedules.id"), primary_key=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), primary_key=True
    )

    schedule: Mapped["Schedule"] = relationship(back_populates="customers")
    customer: Mapped["Customer"] = relationship(back_populates="schedules")


class ScheduleMeasure(Base):
    __tablename__ = "schedule_measure"

    id: Mapped[uuid.UUID] = primary_key()
    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schedules.id"), nullable=False
    )
    measure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("measures.id"), nullable=False
    )
    time_of_day: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    custom_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    schedule: Mapped["Schedule"] = relationship(back_populates="measures")
    measure: Mapped["Measure"] = relationship(back_populates="schedules")


class ScheduleArchive(Base):
    """Snapshot of a schedule at the time of archiving, stored as JSONB."""

    __tablename__ = "schedule_archives"

    id: Mapped[uuid.UUID] = primary_key()
    original_schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    original_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    shift_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    custom_shift: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    archived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ---------------------------------------------------------------------------
# Care Visits
# ---------------------------------------------------------------------------


class CareVisit(Base):
    __tablename__ = "care_visits"

    id: Mapped[uuid.UUID] = primary_key()
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    status: Mapped[
        Literal[
            "planned",
            "completed",
            "canceled",
            "no_show",
            "partially_completed",
            "rescheduled",
        ]
    ] = mapped_column(String, nullable=False, default="planned")
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schedules.id"), nullable=False
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_care_visit_date", "date"),
        Index("ix_care_visit_status", "status"),
        Index("ix_care_visit_customer_date", "customer_id", "date"),
        Index("ix_care_visit_status_date", "status", "date"),
        Index("ix_care_visit_schedule_date", "schedule_id", "date"),
    )

    schedule: Mapped["Schedule"] = relationship("Schedule", back_populates="care_visits")
    customer: Mapped["Customer"] = relationship(back_populates="care_visits")
    employees: Mapped[list["EmployeeCareVisit"]] = relationship(
        back_populates="care_visit"
    )
    measures: Mapped[list["MeasureCareVisit"]] = relationship(
        back_populates="care_visit"
    )


# ---------------------------------------------------------------------------
# Absences
# ---------------------------------------------------------------------------


class Absence(Base):
    __tablename__ = "absences"

    id: Mapped[uuid.UUID] = primary_key()
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False
    )
    absence_type: Mapped[
        Literal["sick", "vab", "vacation", "parental_leave", "leave_of_absence"]
    ] = mapped_column(String, nullable=False)
    start_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    end_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_absence_employee_id", "employee_id"),
        Index("ix_absence_employee_dates", "employee_id", "start_date", "end_date"),
    )

    employee: Mapped["Employee"] = relationship(back_populates="absences")
