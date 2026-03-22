import uuid

from fastapi import status

from api_core import ApiError, api_exception_handler


class ScheduleNotFound(Exception):
    def __init__(self, schedule_id: uuid.UUID) -> None:
        self.schedule_id = schedule_id
        super().__init__(f"Schedule {schedule_id} not found")


class ScheduleConflict(Exception):
    def __init__(self, date: str, shift_type: str) -> None:
        self.date = date
        self.shift_type = shift_type
        super().__init__(f"A {shift_type} schedule for {date} already exists")


class EmployeeAlreadyOnSchedule(Exception):
    def __init__(self, employee_id: uuid.UUID, schedule_id: uuid.UUID) -> None:
        self.employee_id = employee_id
        self.schedule_id = schedule_id
        super().__init__(f"Employee {employee_id} is already on schedule {schedule_id}")


class EmployeeNotOnSchedule(Exception):
    def __init__(self, employee_id: uuid.UUID, schedule_id: uuid.UUID) -> None:
        self.employee_id = employee_id
        self.schedule_id = schedule_id
        super().__init__(f"Employee {employee_id} is not on schedule {schedule_id}")


class CustomerAlreadyOnSchedule(Exception):
    def __init__(self, customer_id: uuid.UUID, schedule_id: uuid.UUID) -> None:
        self.customer_id = customer_id
        self.schedule_id = schedule_id
        super().__init__(f"Customer {customer_id} is already on schedule {schedule_id}")


class CustomerNotOnSchedule(Exception):
    def __init__(self, customer_id: uuid.UUID, schedule_id: uuid.UUID) -> None:
        self.customer_id = customer_id
        self.schedule_id = schedule_id
        super().__init__(f"Customer {customer_id} is not on schedule {schedule_id}")


class ScheduleMeasureNotFound(Exception):
    def __init__(self, schedule_measure_id: uuid.UUID) -> None:
        self.schedule_measure_id = schedule_measure_id
        super().__init__(f"Planned measure {schedule_measure_id} not found")


class MeasureAlreadyOnSchedule(Exception):
    def __init__(self, customer_id: uuid.UUID, measure_id: uuid.UUID) -> None:
        self.customer_id = customer_id
        self.measure_id = measure_id
        super().__init__(
            f"Measure {measure_id} is already planned for customer "
            f"{customer_id} on this schedule"
        )


class CustomerNotOnScheduleForMeasure(Exception):
    """Raised when adding a measure for a customer not assigned to the schedule."""

    def __init__(self, customer_id: uuid.UUID, schedule_id: uuid.UUID) -> None:
        self.customer_id = customer_id
        self.schedule_id = schedule_id
        super().__init__(
            f"Customer {customer_id} is not assigned to schedule {schedule_id}"
        )


class EmployeeAbsenceConflict(Exception):
    """Raised when employee has an absence covering the schedule date."""

    def __init__(
        self,
        employee_id: uuid.UUID,
        schedule_id: uuid.UUID,
        absence_id: uuid.UUID,
    ) -> None:
        self.employee_id = employee_id
        self.schedule_id = schedule_id
        self.absence_id = absence_id
        super().__init__(
            f"Employee {employee_id} has an absence ({absence_id}) "
            f"covering the schedule date"
        )


# --- API error mappings ---


@api_exception_handler(ScheduleNotFound, status.HTTP_404_NOT_FOUND)
class ScheduleNotFoundError(ApiError):
    detail: str

    @classmethod
    def from_original_error(cls, e: ScheduleNotFound) -> "ScheduleNotFoundError":
        return cls(detail=f"Schedule {e.schedule_id} not found")


@api_exception_handler(ScheduleConflict, status.HTTP_409_CONFLICT)
class ScheduleConflictError(ApiError):
    detail: str

    @classmethod
    def from_original_error(cls, e: ScheduleConflict) -> "ScheduleConflictError":
        return cls(detail=f"A {e.shift_type} schedule for {e.date} already exists")


@api_exception_handler(EmployeeAlreadyOnSchedule, status.HTTP_409_CONFLICT)
class EmployeeAlreadyOnScheduleError(ApiError):
    detail: str

    @classmethod
    def from_original_error(
        cls, e: EmployeeAlreadyOnSchedule
    ) -> "EmployeeAlreadyOnScheduleError":
        return cls(detail=f"Employee {e.employee_id} is already on this schedule")


@api_exception_handler(EmployeeNotOnSchedule, status.HTTP_404_NOT_FOUND)
class EmployeeNotOnScheduleError(ApiError):
    detail: str

    @classmethod
    def from_original_error(
        cls, e: EmployeeNotOnSchedule
    ) -> "EmployeeNotOnScheduleError":
        return cls(detail=f"Employee {e.employee_id} is not on this schedule")


@api_exception_handler(CustomerAlreadyOnSchedule, status.HTTP_409_CONFLICT)
class CustomerAlreadyOnScheduleError(ApiError):
    detail: str

    @classmethod
    def from_original_error(
        cls, e: CustomerAlreadyOnSchedule
    ) -> "CustomerAlreadyOnScheduleError":
        return cls(detail=f"Customer {e.customer_id} is already on this schedule")


@api_exception_handler(CustomerNotOnSchedule, status.HTTP_404_NOT_FOUND)
class CustomerNotOnScheduleError(ApiError):
    detail: str

    @classmethod
    def from_original_error(
        cls, e: CustomerNotOnSchedule
    ) -> "CustomerNotOnScheduleError":
        return cls(detail=f"Customer {e.customer_id} is not on this schedule")


@api_exception_handler(ScheduleMeasureNotFound, status.HTTP_404_NOT_FOUND)
class ScheduleMeasureNotFoundError(ApiError):
    detail: str

    @classmethod
    def from_original_error(
        cls, e: ScheduleMeasureNotFound
    ) -> "ScheduleMeasureNotFoundError":
        return cls(detail=f"Planned measure {e.schedule_measure_id} not found")


@api_exception_handler(MeasureAlreadyOnSchedule, status.HTTP_409_CONFLICT)
class MeasureAlreadyOnScheduleError(ApiError):
    detail: str

    @classmethod
    def from_original_error(
        cls, e: MeasureAlreadyOnSchedule
    ) -> "MeasureAlreadyOnScheduleError":
        return cls(
            detail="This measure is already planned for this customer on this schedule"
        )


@api_exception_handler(CustomerNotOnScheduleForMeasure, status.HTTP_409_CONFLICT)
class CustomerNotOnScheduleForMeasureError(ApiError):
    detail: str

    @classmethod
    def from_original_error(
        cls, e: CustomerNotOnScheduleForMeasure
    ) -> "CustomerNotOnScheduleForMeasureError":
        return cls(
            detail=(
                f"Customer {e.customer_id} must be assigned to the schedule "
                "before adding measures"
            )
        )


@api_exception_handler(EmployeeAbsenceConflict, status.HTTP_409_CONFLICT)
class EmployeeAbsenceConflictError(ApiError):
    detail: str

    @classmethod
    def from_original_error(
        cls, e: EmployeeAbsenceConflict
    ) -> "EmployeeAbsenceConflictError":
        return cls(
            detail=(
                f"Employee {e.employee_id} has an absence covering this "
                f"schedule date (absence {e.absence_id})"
            )
        )
