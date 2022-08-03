from datetime import datetime
import ipaddress

from pydantic import BaseModel
from pydantic import UUID4
from . import user


class LocationData(BaseModel):
    country: str | None
    region: str | None
    city: str | None
    latitude: float | None
    longitude: float | None


class DeviceInfo(BaseModel):
    family: str | None
    brand: str | None
    model: str | None
    is_mobile: bool | None
    is_tablet: bool | None
    is_pc: bool | None
    supports_touch: bool | None


class OsInfo(BaseModel):
    family: str | None
    version: str | None


class BrowserInfo(BaseModel):
    family: str | None
    version: str | None


class UserAgentInfo(BaseModel):
    is_bot: bool | None
    device: DeviceInfo
    os: OsInfo
    browser: BrowserInfo


class LoginData(BaseModel):
    user_agent: str
    user_agent_info: UserAgentInfo
    ip_address: ipaddress.IPv4Address
    location: LocationData | None


class ReturnActiveSession(BaseModel):
    id: UUID4
    first_accessed: datetime
    last_accessed: datetime
    sign_in_data: LoginData
    last_access_data: LoginData

    class Config:
        orm_mode = True


class ActiveUserSession(BaseModel):
    id: UUID4
    first_accessed: datetime
    last_accessed: datetime
    sign_in_user_agent: str
    sign_in_ip_address: ipaddress.IPv4Address
    last_user_agent: str
    last_ip_address: ipaddress.IPv4Address
    user: user.ReturnUserDetailed

    class Config:
        orm_mode = True
