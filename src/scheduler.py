import pytz
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()


def configure_and_start_scheduler(database_url: str):
    jobstores = {"default": SQLAlchemyJobStore(url=database_url)}

    scheduler.configure(jobstores=jobstores, timezone=pytz.timezone("Europe/Warsaw"))

    if not scheduler.running:
        scheduler.start()

    print(scheduler.running)


def test_sch():
    print(scheduler.running)
