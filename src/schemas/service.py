from datetime import datetime
from pydantic import BaseModel, Field, UUID4, validator
from .user import ReturnUserDetailed
from typing import List, Optional, Union


class Service(BaseModel):
    name: str
    min_price: int = Field(gt=0)
    max_price: int = Field(gt=0)
    average_time_minutes: int
    description: Union[None, str]
    available: bool

    @validator('max_price')
    def validate(cls, v):
        if v.min_price > v.max_price:
            raise ValueError('ensure max_price is greater than the min_price')
        return v

    class Config:
        orm_mode = True


class CreateService(Service):
    description: Optional[str] = None


class CreateServices(BaseModel):
    services: List[Service]


class ReturnService(Service):
    id: UUID4
    created_at: datetime


class ReturnServiceDetailed(ReturnService):
    created_by: ReturnUserDetailed
