from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, UUID4, validator

from .user import ReturnUserDetailed


class Service(BaseModel):
    name: str
    min_price: int = Field(gt=0)
    max_price: int = Field(gt=0)
    average_time_minutes: int
    description: str = Field(min_length=60, max_length=140, default=None)
    available: bool
    required_slots: int

    @validator("max_price")
    def validate(cls, v):
        if v.min_price > v.max_price:
            raise ValueError("ensure max_price is greater than the min_price")
        return v

    class Config:
        orm_mode = True


class CreateService(Service):
    description: Optional[str] = None
    created_at: datetime


class ReturnService(Service):
    id: UUID4


class ReturnServiceDetailed(ReturnService):
    created_by: ReturnUserDetailed


class UpdateService(BaseModel):
    name: str
    min_price: int = Field(gt=0)
    max_price: int = Field(gt=0)
    average_time_minutes: int
    description: str = Field(min_length=60, max_length=140, default=None)
    available: bool
