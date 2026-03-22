import uuid
from datetime import date as date_type

from fastapi import status

from api_core import ApiError, api_exception_handler


class AbsenceNotFound(Exception):
    def __init__(self, absence_id: uuid.UUID) -> None:
        self.absence_id = absence_id
        super().__init__(f"Absence {absence_id} not found")


class AbsenceOverlap(Exception):
    def __init__(
        self,
        employee_id: uuid.UUID,
        start_date: date_type,
        end_date: date_type,
        existing_id: uuid.UUID,
    ) -> None:
        self.employee_id = employee_id
        self.start_date = start_date
        self.end_date = end_date
        self.existing_id = existing_id
        super().__init__(
            f"Absence for employee {employee_id} overlaps with "
            f"existing absence {existing_id} ({start_date} - {end_date})"
        )


class AbsenceInvalidDateRange(Exception):
    def __init__(self, start_date: date_type, end_date: date_type) -> None:
        self.start_date = start_date
        self.end_date = end_date
        super().__init__(f"start_date {start_date} must be <= end_date {end_date}")


# --- API error mappings ---


@api_exception_handler(AbsenceNotFound, status.HTTP_404_NOT_FOUND)
class AbsenceNotFoundError(ApiError):
    detail: str

    @classmethod
    def from_original_error(cls, e: AbsenceNotFound) -> "AbsenceNotFoundError":
        return cls(detail=f"Absence {e.absence_id} not found")


@api_exception_handler(AbsenceOverlap, status.HTTP_409_CONFLICT)
class AbsenceOverlapError(ApiError):
    detail: str

    @classmethod
    def from_original_error(cls, e: AbsenceOverlap) -> "AbsenceOverlapError":
        return cls(
            detail=(
                f"This absence overlaps with existing absence {e.existing_id} "
                f"for the same employee"
            )
        )


@api_exception_handler(AbsenceInvalidDateRange, status.HTTP_422_UNPROCESSABLE_CONTENT)
class AbsenceInvalidDateRangeError(ApiError):
    detail: str

    @classmethod
    def from_original_error(
        cls, e: AbsenceInvalidDateRange
    ) -> "AbsenceInvalidDateRangeError":
        return cls(
            detail=f"start_date ({e.start_date}) must be <= end_date ({e.end_date})"
        )
