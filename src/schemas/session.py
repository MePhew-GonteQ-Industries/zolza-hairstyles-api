import ipaddress
from datetime import datetime

from pydantic import ConfigDict, BaseModel, UUID4

from . import user


class LocationData(BaseModel):
    country: str | None = None
    region: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class DeviceInfo(BaseModel):
    family: str | None = None
    brand: str | None = None
    model: str | None = None
    is_mobile: bool | None = None
    is_tablet: bool | None = None
    is_pc: bool | None = None
    supports_touch: bool | None = None


class OsInfo(BaseModel):
    family: str | None = None
    version: str | None = None


class BrowserInfo(BaseModel):
    family: str | None = None
    version: str | None = None


class UserAgentInfo(BaseModel):
    is_bot: bool | None = None
    device: DeviceInfo
    os: OsInfo
    browser: BrowserInfo


class LoginData(BaseModel):
    user_agent: str
    user_agent_info: UserAgentInfo
    ip_address: ipaddress.IPv4Address
    location: LocationData | None = None


class ReturnActiveSession(BaseModel):
    id: UUID4
    first_accessed: datetime
    last_accessed: datetime
    sign_in_data: LoginData
    last_access_data: LoginData
    model_config = ConfigDict(from_attributes=True)


class ActiveUserSession(BaseModel):
    id: UUID4
    first_accessed: datetime
    last_accessed: datetime
    sign_in_user_agent: str
    sign_in_ip_address: ipaddress.IPv4Address
    last_user_agent: str
    last_ip_address: ipaddress.IPv4Address
    user: user.ReturnUserDetailed
    model_config = ConfigDict(from_attributes=True)
