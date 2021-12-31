from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))


class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, nullable=False)
    user_defined = Column(Boolean, default=False, nullable=False)


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = relationship("User")


class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, nullable=False)
