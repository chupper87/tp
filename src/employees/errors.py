import uuid

from fastapi import status

from api_core import ApiError, api_exception_handler


class EmployeeNotFound(Exception):
    def __init__(self, employee_id: uuid.UUID) -> None:
        self.employee_id = employee_id
        super().__init__(f"Employee {employee_id} not found")


class EmailAlreadyInUse(Exception):
    pass


@api_exception_handler(EmployeeNotFound, status.HTTP_404_NOT_FOUND)
class EmployeeNotFoundError(ApiError):
    detail: str

    @classmethod
    def from_original_error(cls, e: EmployeeNotFound) -> "EmployeeNotFoundError":
        return cls(detail=f"Employee {e.employee_id} not found")


@api_exception_handler(EmailAlreadyInUse, status.HTTP_409_CONFLICT)
class EmailAlreadyInUseError(ApiError):
    detail: str = "A user with this email already exists"

    @classmethod
    def from_original_error(cls, e: EmailAlreadyInUse) -> "EmailAlreadyInUseError":
        return cls()
