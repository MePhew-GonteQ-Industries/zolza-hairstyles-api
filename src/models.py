import enum
from enum import auto

from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import ARRAY, DATE, TIMESTAMP

from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    email = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    permission_level = Column(
        ARRAY(item_type=String), nullable=False, server_default="{user}"
    )
    verified = Column(Boolean, nullable=False, server_default="false")
    disabled = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(
        TIMESTAMP(timezone=False), nullable=False, server_default=text("now()")
    )
    settings = relationship("Setting")


class Password(Base):
    __tablename__ = "passwords"
    id = Column(Integer, primary_key=True, nullable=False)
    password_hash = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    current = Column(Boolean, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=False), nullable=False, server_default=text("now()")
    )


class Session(Base):
    __tablename__ = "sessions"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    sign_in_user_agent = Column(String, nullable=False)
    sign_in_ip_address = Column(String, nullable=False)
    last_user_agent = Column(String, nullable=False)
    last_ip_address = Column(String, nullable=False)
    last_accessed = Column(
        TIMESTAMP(timezone=False), nullable=False, server_default=text("now()")
    )
    sudo_mode_activated = Column(TIMESTAMP(timezone=False))
    sudo_mode_expires = Column(TIMESTAMP(timezone=False))
    first_accessed = Column(
        TIMESTAMP(timezone=False), nullable=False, server_default=text("now()")
    )


class EmailRequests(Base):
    __tablename__ = "email_requests"
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    request_type = Column(String, nullable=False)
    request_token = Column(String, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=False), nullable=False, server_default=text("now()")
    )
    UniqueConstraint("user_id", "request_type", name="limit_email_requests")


class Service(Base):
    __tablename__ = "services"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    min_price = Column(Integer, nullable=False)
    max_price = Column(Integer, nullable=False)
    average_time_minutes = Column(Integer, nullable=False)
    required_slots = Column(Integer, nullable=False)
    available = Column(Boolean, nullable=False, server_default=text("true"))
    deleted = Column(Boolean, nullable=False, server_default=text("false"))
    created_at = Column(
        TIMESTAMP(timezone=False), nullable=False, server_default=text("now()")
    )


class ServiceTranslations(Base):
    __tablename__ = "service_translations"
    id = Column(Integer, primary_key=True, nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    UniqueConstraint("service_id", "language_id", name="one_translation_per_language")
    service = relationship("Service")


class ServiceEvent(Base):
    __tablename__ = "service_events"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    event_type = Column(String, nullable=False)
    performed_by_user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    performed_on_service_id = Column(
        UUID(as_uuid=True), ForeignKey("services.id"), nullable=False
    )
    performed_by = relationship("User", foreign_keys=[performed_by_user_id])
    performed_on = relationship("Service", foreign_keys=[performed_on_service_id])
    performed_at = Column(
        TIMESTAMP(timezone=False), nullable=False, server_default=text("now()")
    )


class PermissionEventType(enum.Enum):
    user_ban = auto()
    user_unban = auto()


class PermissionEvent(Base):
    __tablename__ = "permission_events"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    event_type = Column(
        Enum(PermissionEventType, name="permission_event_type"), nullable=False
    )
    performed_by_user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    performed_on_user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    performed_by = relationship("User", foreign_keys=[performed_by_user_id])
    performed_on = relationship("User", foreign_keys=[performed_on_user_id])
    performed_at = Column(
        TIMESTAMP(timezone=False), nullable=False, server_default=text("now()")
    )


class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    occupied = Column(Boolean, nullable=False, server_default="false")
    occupied_by_appointment = Column(
        UUID(as_uuid=True), ForeignKey("appointments.id", use_alter=True)
    )
    reserved = Column(Boolean, nullable=False, server_default="false")
    reserved_reason = Column(String)
    holiday = Column(Boolean, nullable=False, server_default="false")
    sunday = Column(Boolean, nullable=False, server_default="false")
    break_time = Column(Boolean, nullable=False, server_default="false")
    holiday_id = Column(Integer, ForeignKey("holidays.id"))
    date = Column(DATE, nullable=False)
    start_time = Column(TIMESTAMP(timezone=False), unique=True)
    end_time = Column(TIMESTAMP(timezone=False), unique=True)
    appointment = relationship(
        "Appointment",
        cascade="all,delete",
        backref="parent",
        foreign_keys=[occupied_by_appointment],
    )
    holiday_info = relationship("Holiday")


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    start_slot_id = Column(
        UUID(as_uuid=True), ForeignKey("appointment_slots.id"), nullable=False
    )
    end_slot_id = Column(
        UUID(as_uuid=True), ForeignKey("appointment_slots.id"), nullable=False
    )
    canceled = Column(Boolean, nullable=False, server_default="false")
    archival = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(
        TIMESTAMP(timezone=False), nullable=False, server_default=text("now()")
    )
    start_slot = relationship(
        "AppointmentSlot", cascade="all,delete", foreign_keys=[start_slot_id]
    )
    end_slot = relationship(
        "AppointmentSlot", cascade="all,delete", foreign_keys=[end_slot_id]
    )
    service = relationship("Service")


class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    default_value = Column(String)
    current_value = Column(String, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=False), nullable=False, server_default=text("now()")
    )
    UniqueConstraint("user_id", "name", name="unique_user_settings")


class Holiday(Base):
    __tablename__ = "holidays"
    id = Column(Integer, primary_key=True, nullable=False)
    translation = relationship("HolidayTranslations")


class HolidayTranslations(Base):
    __tablename__ = "holiday_translations"
    id = Column(Integer, primary_key=True, nullable=False)
    holiday_id = Column(Integer, ForeignKey("holidays.id"), nullable=False)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    name = Column(String, nullable=False, unique=True)
    UniqueConstraint("holiday_id", "language_id", name="one_translation_per_language")


class Language(Base):
    __tablename__ = "languages"
    id = Column(Integer, primary_key=True, nullable=False)
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False, unique=True)
