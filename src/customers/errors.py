import uuid

from fastapi import status

from api_core import ApiError, api_exception_handler


class CustomerNotFound(Exception):
    def __init__(self, customer_id: uuid.UUID) -> None:
        self.customer_id = customer_id
        super().__init__(f"Customer {customer_id} not found")


class KeyNumberAlreadyInUse(Exception):
    def __init__(self, key_number: int) -> None:
        self.key_number = key_number
        super().__init__(f"Key number {key_number} is already in use")


@api_exception_handler(CustomerNotFound, status.HTTP_404_NOT_FOUND)
class CustomerNotFoundError(ApiError):
    detail: str

    @classmethod
    def from_original_error(cls, e: CustomerNotFound) -> "CustomerNotFoundError":
        return cls(detail=f"Customer {e.customer_id} not found")


@api_exception_handler(KeyNumberAlreadyInUse, status.HTTP_409_CONFLICT)
class KeyNumberAlreadyInUseError(ApiError):
    detail: str

    @classmethod
    def from_original_error(
        cls, e: KeyNumberAlreadyInUse
    ) -> "KeyNumberAlreadyInUseError":
        return cls(detail=f"Key number {e.key_number} is already in use")
