from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from src.database import database_engine
from src.utils import PL_TIMEZONE

scheduler = BackgroundScheduler()


def configure_and_start_scheduler():
    if not scheduler.running:
        jobstores = {"default": SQLAlchemyJobStore(engine=database_engine)}

        scheduler.configure(jobstores=jobstores, timezone=PL_TIMEZONE)

        scheduler.start()
