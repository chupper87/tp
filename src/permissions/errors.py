import uuid

from fastapi import status

from api_core import ApiError, api_exception_handler


class PermissionNotFound(Exception):
    def __init__(self, permission_id: uuid.UUID) -> None:
        self.permission_id = permission_id
        super().__init__(f"Permission {permission_id} not found")


class PermissionDuplicate(Exception):
    def __init__(self, principal: str, resource: str) -> None:
        self.principal = principal
        self.resource = resource
        super().__init__(
            f"Permission already exists for principal {principal} on resource {resource}"
        )


# --- API error mappings ---


@api_exception_handler(PermissionNotFound, status.HTTP_404_NOT_FOUND)
class PermissionNotFoundError(ApiError):
    detail: str

    @classmethod
    def from_original_error(cls, e: PermissionNotFound) -> "PermissionNotFoundError":
        return cls(detail=f"Permission {e.permission_id} not found")


@api_exception_handler(PermissionDuplicate, status.HTTP_409_CONFLICT)
class PermissionDuplicateError(ApiError):
    detail: str

    @classmethod
    def from_original_error(cls, e: PermissionDuplicate) -> "PermissionDuplicateError":
        return cls(
            detail=(
                f"Permission already exists for {e.principal} on {e.resource}. "
                "Use PATCH to change the action level."
            )
        )
