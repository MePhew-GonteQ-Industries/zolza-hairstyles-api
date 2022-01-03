from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP, ARRAY
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    permission_level = Column(ARRAY(item_type=String), nullable=False, server_default='{user}')
    disabled = Column(Boolean, nullable=False, server_default='false')
    verified = Column(Boolean, nullable=False, server_default='false')
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))


class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    available = Column(Boolean, nullable=False, server_default='true')
    user_defined = Column(Boolean, nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, nullable=False)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    scheduled_for = Column(TIMESTAMP(timezone=True), nullable=False)
    canceled = Column(Boolean, nullable=False, server_default='false')
    archival = Column(Boolean, nullable=False, server_default='false')
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))


class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    default_value = Column(String)
    current_value = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))
    UniqueConstraint('user_id', 'name', name='unique_user_settings')
