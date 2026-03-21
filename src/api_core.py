from abc import ABC, abstractmethod
from typing import Any, Self, TypeVar, Union
import itertools

from fastapi import status  # noqa: F401
from pydantic import BaseModel

from log_setup import get_logger

log = get_logger(__name__)


class GenericAPIResponse(BaseModel):
    detail: str


class ApiError(BaseModel, ABC):
    """
    Abstract base class for API errors.

    Register with @api_exception_handler to map internal exceptions
    to HTTP responses — keeps internal details away from the client.

    Example:
        @api_exception_handler(MyInternalError, status.HTTP_400_BAD_REQUEST)
        class MyApiError(ApiError):
            message: str = "Something went wrong"

            @classmethod
            def from_original_error(cls, e: MyInternalError):
                return cls()
    """

    @classmethod
    @abstractmethod
    def from_original_error(cls, e) -> Self:
        _ = e
        return cls()


__api_exception_handlers: dict[type[Exception], tuple[type[ApiError], int]] = {}
__status_code_for_api_error: dict[type[ApiError], int] = {}

ExceptionT = TypeVar("ExceptionT")


def api_exception_handler(
    exception_class: type[Exception],
    status_code: int,
):
    def inner(f: type[ApiError]):
        __api_exception_handlers[exception_class] = (f, status_code)
        __status_code_for_api_error[f] = status_code
        return f

    return inner


def responses_from_api_errors(
    *api_errors: type[ApiError],
) -> dict[Union[int, str], dict[str, Any]]:
    if not api_errors:
        raise ValueError("At least one ApiError must be provided")

    for api_error in api_errors:
        if not issubclass(api_error, ApiError):
            raise ValueError(f"Invalid type, must be ApiError, got {type(api_error)}")

    def model_from_errors(errors):
        tup = tuple(errors)
        if len(tup) > 1:
            return Union[tup]  # type: ignore
        return tup[0]

    return {
        status_code: {"model": model_from_errors(errors)}
        for status_code, errors in itertools.groupby(
            api_errors,
            lambda x: __status_code_for_api_error[x],
        )
    }
