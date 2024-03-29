from datetime import datetime
from enum import Enum

from pydantic import ConfigDict, BaseModel, UUID4

from .service import ReturnServiceDetailed
from .user import ReturnUserDetailed


class EventType(str, Enum):
    create = "create"
    update = "update"
    delete = "delete"


class Event(BaseModel):
    id: UUID4
    event_type: EventType
    model_config = ConfigDict(from_attributes=True)


class CreateServiceEvent(Event):
    performed_by_user_id: UUID4
    performed_on_service_id: UUID4


class ReturnServiceEvent(Event):
    performed_by: ReturnUserDetailed
    performed_on: ReturnServiceDetailed
    performed_at: datetime


class CreatePermissionEvent(Event):
    performed_by_user_id: UUID4
    performed_on_user_id: UUID4


class ReturnPermissionEvent(Event):
    performed_by: ReturnUserDetailed
    performed_on: ReturnUserDetailed
    performed_at: datetime
