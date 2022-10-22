from pydantic import BaseModel


class ServiceStats(BaseModel):
    registered_users: int
    total_appointments: int
    upcoming_appointments: int
    archival_appointments: int
