import datetime

from pydantic import BaseModel, UUID4


class AppointmentSlot(BaseModel):
    id: UUID4
    occupied: bool
    reserved: bool
    reserved_reason: str | None
    holiday: bool
    sunday: bool
    break_time: bool
    date: datetime.date
    start_time: datetime.datetime | None
    end_time: datetime.datetime | None
    holiday_name: str | None

    class Config:
        orm_mode = True


class AppointmentSlotDetailed(AppointmentSlot):
    occupied_by_appointment: None | UUID4


class BaseAppointment(BaseModel):
    service_id: UUID4

    class Config:
        orm_mode = True


class CreateAppointment(BaseAppointment):
    first_slot_id: UUID4


class ReturnAppointment(BaseAppointment):
    pass
