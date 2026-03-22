import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

ActionField = Literal["read", "write", "admin"]


class PermissionCreate(BaseModel):
    principal: str
    resource: str
    action: ActionField


class PermissionUpdate(BaseModel):
    action: ActionField


class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    principal: str
    resource: str
    action: str
    created_by: uuid.UUID
    created_at: datetime
