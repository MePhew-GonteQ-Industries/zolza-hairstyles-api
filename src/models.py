from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'))
    email = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    permission_level = Column(ARRAY(item_type=String), nullable=False, server_default='{user}')
    verified = Column(Boolean, nullable=False, server_default='false')
    disabled = Column(Boolean, nullable=False, server_default='false')
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))
    settings = relationship('Setting')


class Password(Base):
    __tablename__ = 'passwords'
    id = Column(Integer, primary_key=True, nullable=False)
    password_hash = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    current = Column(Boolean, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))


class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))


class EmailRequests(Base):
    __tablename__ = 'email_requests'
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    request_type = Column(String, nullable=False)
    request_token = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))
    UniqueConstraint('user_id', 'request_type', name='limit_email_requests')


class Service(Base):
    __tablename__ = "services"
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'))
    name = Column(String, nullable=False, unique=True)
    min_price = Column(Integer, nullable=False)
    max_price = Column(Integer, nullable=False)
    average_time_minutes = Column(Integer, nullable=False)
    description = Column(String)
    available = Column(Boolean, nullable=False)
    deleted = Column(Boolean, nullable=False, server_default=text('false'))
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    created_by = relationship("User")
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))


class ServiceEvent(Base):
    __tablename__ = 'service_events'
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'))
    event_type = Column(String, nullable=False)
    performed_by_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    performed_on_service_id = Column(UUID(as_uuid=True), ForeignKey('services.id'), nullable=False)
    performed_by = relationship('User', foreign_keys=[performed_by_user_id])
    performed_on = relationship('Service', foreign_keys=[performed_on_service_id])
    performed_at = Column(TIMESTAMP(timezone=True),
                          nullable=False, server_default=text('now()'))


class PermissionEvent(Base):
    __tablename__ = 'permission_events'
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'))
    event_type = Column(String, nullable=False)
    performed_by_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    performed_on_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    performed_by = relationship('User', foreign_keys=[performed_by_user_id])
    performed_on = relationship('User', foreign_keys=[performed_on_user_id])
    performed_at = Column(TIMESTAMP(timezone=True),
                          nullable=False, server_default=text('now()'))


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'))
    service_id = Column(UUID(as_uuid=True), ForeignKey('services.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    scheduled_for = Column(TIMESTAMP(timezone=True), nullable=False)
    canceled = Column(Boolean, nullable=False, server_default='false')
    archival = Column(Boolean, nullable=False, server_default='false')
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))


class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    default_value = Column(String)
    current_value = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))
    UniqueConstraint('user_id', 'name', name='unique_user_settings')
