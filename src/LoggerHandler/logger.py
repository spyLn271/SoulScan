import logging
from logging.handlers import RotatingFileHandler

def setup_logger(level=logging.INFO, log_file="app.log", logger_name=__name__):
    logger = logging.getLogger(logger_name)
    if logger.hasHandlers():
        return logger

    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)'
    )

    file_handler = RotatingFileHandler(log_file, maxBytes=2 * 1024 * 1024, backupCount=10, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info(f"Logger '{logger_name}' initialized and is now online.")
    return logger

def get_logger(logger_name=__name__):
    return logging.getLogger(logger_name)
