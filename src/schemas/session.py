from datetime import datetime
import ipaddress

from pydantic import BaseModel
from pydantic import UUID4
from . import user


class Session(BaseModel):
    user_id: UUID4
    access_token: str
    refresh_token: str
    sign_in_user_agent: str
    sign_in_ip_address: str
    last_user_agent: str
    last_ip_address: str

    class Config:
        orm_mode = True


class ReturnActiveSession(BaseModel):
    id: UUID4
    first_accessed: datetime
    last_accessed: datetime
    sign_in_user_agent: str
    sign_in_ip_address: ipaddress.IPv4Address
    sign_in_city: str | None
    sign_in_region: str | None
    sign_in_country: str | None
    sign_in_location: str | None
    last_user_agent: str
    last_ip_address: ipaddress.IPv4Address
    last_city: str | None
    last_region: str | None
    last_country: str | None
    last_location: str | None

    class Config:
        orm_mode = True


class NewUserSession(BaseModel):
    id: UUID4
    user_agent: str
    ip_address: str
    user: user.ReturnUserDetailed
