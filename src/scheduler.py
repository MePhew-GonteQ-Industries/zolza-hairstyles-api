import pytz
from .database import SQLALCHEMY_DATABASE_URL
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore


jobstores = {
    'default': SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URL)
}

scheduler = BackgroundScheduler()

scheduler.configure(jobstores=jobstores, timezone=pytz.timezone('Europe/Warsaw'))
