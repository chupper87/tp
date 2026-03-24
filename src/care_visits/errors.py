import uuid

from fastapi import status

from api_core import ApiError, api_exception_handler


class CareVisitNotFound(Exception):
    def __init__(self, care_visit_id: uuid.UUID) -> None:
        self.care_visit_id = care_visit_id
        super().__init__(f"Care visit {care_visit_id} not found")


class EmployeeNotOnScheduleForVisit(Exception):
    """Employee must be assigned to the schedule before being added to a visit."""

    def __init__(self, employee_id: uuid.UUID, schedule_id: uuid.UUID) -> None:
        self.employee_id = employee_id
        self.schedule_id = schedule_id
        super().__init__(
            f"Employee {employee_id} is not assigned to schedule {schedule_id}"
        )


class CustomerNotOnScheduleForVisit(Exception):
    """Customer must be assigned to the schedule to create a visit."""

    def __init__(self, customer_id: uuid.UUID, schedule_id: uuid.UUID) -> None:
        self.customer_id = customer_id
        self.schedule_id = schedule_id
        super().__init__(
            f"Customer {customer_id} is not assigned to schedule {schedule_id}"
        )


class EmployeeAlreadyOnVisit(Exception):
    def __init__(self, employee_id: uuid.UUID, care_visit_id: uuid.UUID) -> None:
        self.employee_id = employee_id
        self.care_visit_id = care_visit_id
        super().__init__(
            f"Employee {employee_id} is already on care visit {care_visit_id}"
        )


class EmployeeNotOnVisit(Exception):
    def __init__(self, employee_id: uuid.UUID, care_visit_id: uuid.UUID) -> None:
        self.employee_id = employee_id
        self.care_visit_id = care_visit_id
        super().__init__(f"Employee {employee_id} is not on care visit {care_visit_id}")


class InvalidStatusTransition(Exception):
    def __init__(self, current: str, requested: str) -> None:
        self.current = current
        self.requested = requested
        super().__init__(f"Cannot transition from '{current}' to '{requested}'")


class CareVisitMustHaveEmployee(Exception):
    """A care visit cannot have zero employees."""

    def __init__(self, care_visit_id: uuid.UUID) -> None:
        self.care_visit_id = care_visit_id
        super().__init__(f"Care visit {care_visit_id} must have at least one employee")


class OverlappingVisit(Exception):
    """A visit overlaps with an existing visit for the same employee."""

    def __init__(self, employee_id: uuid.UUID, existing_visit_id: uuid.UUID) -> None:
        self.employee_id = employee_id
        self.existing_visit_id = existing_visit_id
        super().__init__(
            f"Visit overlaps with existing visit {existing_visit_id} "
            f"for employee {employee_id}"
        )


class MeasureAlreadyAssignedToVisit(Exception):
    """A schedule measure is already linked to another care visit."""

    def __init__(self, schedule_measure_id: uuid.UUID, care_visit_id: uuid.UUID) -> None:
        self.schedule_measure_id = schedule_measure_id
        self.care_visit_id = care_visit_id
        super().__init__(
            f"Schedule measure {schedule_measure_id} is already assigned "
            f"to care visit {care_visit_id}"
        )


# --- API error mappings ---


@api_exception_handler(CareVisitNotFound, status.HTTP_404_NOT_FOUND)
class CareVisitNotFoundError(ApiError):
    detail: str

    @classmethod
    def from_original_error(cls, e: CareVisitNotFound) -> "CareVisitNotFoundError":
        return cls(detail=f"Care visit {e.care_visit_id} not found")


@api_exception_handler(EmployeeNotOnScheduleForVisit, status.HTTP_409_CONFLICT)
class EmployeeNotOnScheduleForVisitError(ApiError):
    detail: str

    @classmethod
    def from_original_error(
        cls, e: EmployeeNotOnScheduleForVisit
    ) -> "EmployeeNotOnScheduleForVisitError":
        return cls(
            detail=(
                f"Employee {e.employee_id} must be assigned to the schedule "
                "before being added to a visit"
            )
        )


@api_exception_handler(CustomerNotOnScheduleForVisit, status.HTTP_409_CONFLICT)
class CustomerNotOnScheduleForVisitError(ApiError):
    detail: str

    @classmethod
    def from_original_error(
        cls, e: CustomerNotOnScheduleForVisit
    ) -> "CustomerNotOnScheduleForVisitError":
        return cls(
            detail=(
                f"Customer {e.customer_id} must be assigned to the schedule "
                "before creating a visit"
            )
        )


@api_exception_handler(EmployeeAlreadyOnVisit, status.HTTP_409_CONFLICT)
class EmployeeAlreadyOnVisitError(ApiError):
    detail: str

    @classmethod
    def from_original_error(
        cls, e: EmployeeAlreadyOnVisit
    ) -> "EmployeeAlreadyOnVisitError":
        return cls(detail=f"Employee {e.employee_id} is already on this visit")


@api_exception_handler(EmployeeNotOnVisit, status.HTTP_404_NOT_FOUND)
class EmployeeNotOnVisitError(ApiError):
    detail: str

    @classmethod
    def from_original_error(cls, e: EmployeeNotOnVisit) -> "EmployeeNotOnVisitError":
        return cls(detail=f"Employee {e.employee_id} is not on this visit")


@api_exception_handler(InvalidStatusTransition, status.HTTP_409_CONFLICT)
class InvalidStatusTransitionError(ApiError):
    detail: str

    @classmethod
    def from_original_error(
        cls, e: InvalidStatusTransition
    ) -> "InvalidStatusTransitionError":
        return cls(detail=f"Cannot transition from '{e.current}' to '{e.requested}'")


@api_exception_handler(CareVisitMustHaveEmployee, status.HTTP_409_CONFLICT)
class CareVisitMustHaveEmployeeError(ApiError):
    detail: str

    @classmethod
    def from_original_error(
        cls, e: CareVisitMustHaveEmployee
    ) -> "CareVisitMustHaveEmployeeError":
        return cls(detail="A care visit must have at least one employee")


@api_exception_handler(OverlappingVisit, status.HTTP_409_CONFLICT)
class OverlappingVisitError(ApiError):
    detail: str

    @classmethod
    def from_original_error(cls, e: OverlappingVisit) -> "OverlappingVisitError":
        return cls(
            detail=(
                f"Visit overlaps with existing visit {e.existing_visit_id} "
                f"for employee {e.employee_id}"
            )
        )


@api_exception_handler(MeasureAlreadyAssignedToVisit, status.HTTP_409_CONFLICT)
class MeasureAlreadyAssignedToVisitError(ApiError):
    detail: str

    @classmethod
    def from_original_error(
        cls, e: MeasureAlreadyAssignedToVisit
    ) -> "MeasureAlreadyAssignedToVisitError":
        return cls(
            detail=(
                f"Schedule measure {e.schedule_measure_id} is already "
                f"assigned to another visit"
            )
        )
