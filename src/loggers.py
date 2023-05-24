import logging

from .config import settings

LOG_FILE_ENCODING = 'utf-8'

# Common handlers and formatters
file_log_formatter = logging.Formatter(
    "%(threadName)s; %(asctime)s; %(levelname)s; %(message)s",
    "%Y-%m-%d %H:%M:%S",
)

error_log_file_handler = logging.FileHandler('app-error.log',
                                             encoding=LOG_FILE_ENCODING)
error_log_file_handler.setFormatter(file_log_formatter)
error_log_file_handler.setLevel(logging.ERROR)

general_log_file_handler = logging.FileHandler('app.log',
                                               encoding=LOG_FILE_ENCODING)
general_log_file_handler.setFormatter(file_log_formatter)

stream_log_formatter = logging.Formatter(
    "%(threadName)s; %(asctime)s; %(levelname)s; %(message)s",
    "%H:%M:%S",
)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(stream_log_formatter)

# Main app logger
app_logger = logging.getLogger('app-logger')
app_logger.setLevel(settings.LOG_LEVEL)

app_logger.addHandler(general_log_file_handler)
app_logger.addHandler(error_log_file_handler)
app_logger.addHandler(stream_handler)

# Additional logger only for app initialization
init_app_file_handler = logging.FileHandler("init_app.log")
init_app_file_handler.setFormatter(file_log_formatter)

init_app_logger = logging.getLogger('init-app-logger')
init_app_logger.setLevel(settings.LOG_LEVEL)
init_app_logger.addHandler(init_app_file_handler)
