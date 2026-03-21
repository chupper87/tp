import uuid

from fastapi import status

from api_core import ApiError, api_exception_handler


class MeasureNotFound(Exception):
    def __init__(self, measure_id: uuid.UUID) -> None:
        self.measure_id = measure_id
        super().__init__(f"Measure {measure_id} not found")


class MeasureNameAlreadyInUse(Exception):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"A measure named '{name}' already exists")


@api_exception_handler(MeasureNotFound, status.HTTP_404_NOT_FOUND)
class MeasureNotFoundError(ApiError):
    detail: str

    @classmethod
    def from_original_error(cls, e: MeasureNotFound) -> "MeasureNotFoundError":
        return cls(detail=f"Measure {e.measure_id} not found")


@api_exception_handler(MeasureNameAlreadyInUse, status.HTTP_409_CONFLICT)
class MeasureNameAlreadyInUseError(ApiError):
    detail: str

    @classmethod
    def from_original_error(
        cls, e: MeasureNameAlreadyInUse
    ) -> "MeasureNameAlreadyInUseError":
        return cls(detail=f"A measure named '{e.name}' already exists")
