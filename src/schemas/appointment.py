import datetime

from pydantic import field_validator, ConfigDict, BaseModel, UUID4

from src.schemas.service import ReturnService
from src.schemas.user import ReturnUserDetailed


class AppointmentSlot(BaseModel):
    id: UUID4
    occupied: bool
    reserved: bool
    reserved_reason: str | None = None
    holiday: bool
    sunday: bool
    break_time: bool
    date: datetime.date
    start_time: datetime.datetime | None = None
    end_time: datetime.datetime | None = None
    holiday_name: str | None = None
    model_config = ConfigDict(from_attributes=True)


class AppointmentSlotDetailed(AppointmentSlot):
    occupied_by_appointment: None | UUID4 = None


class BaseAppointment(BaseModel):
    service_id: UUID4
    model_config = ConfigDict(from_attributes=True)


class FirstSlot(BaseModel):
    first_slot_id: UUID4
    model_config = ConfigDict(from_attributes=True)


class CreateAppointment(BaseAppointment, FirstSlot):
    pass


class ReturnAppointment(BaseModel):
    id: UUID4
    canceled: bool
    archival: bool
    created_at: datetime.datetime
    start_slot: AppointmentSlot
    end_slot: AppointmentSlot
    service: ReturnService
    model_config = ConfigDict(from_attributes=True)


class ReturnAppointmentDetailed(ReturnAppointment):
    user: ReturnUserDetailed


class ReturnAllAppointments(BaseModel):
    items: list[ReturnAppointmentDetailed]
    total: int


class SlotsReservation(BaseModel):
    slots: list[UUID4]

    @field_validator("slots")
    @classmethod
    def validate_slots(cls, v):
        if len(set(v)) != len(v):
            raise ValueError("ensure all slots are unique")

        return v


class ReserveSlots(SlotsReservation):
    reason: str = None


class UnreserveSlots(SlotsReservation):
    pass
