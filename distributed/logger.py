import os
import logging
from datetime import datetime


def default_formatter():
    _fmt = '%(asctime)s | %(levelname)8s | %(process)d | %(message)s'
    _datefmt = '%b %d %H:%M:%S'
    return logging.Formatter(fmt=_fmt, datefmt=_datefmt)


def _file_handler(pattern=''):
    file_handler = logging.FileHandler(
        filename=datetime.now().strftime(f'_logs/{pattern}_%b_%d_%m_%Y.log'))
    file_handler.setFormatter(default_formatter())
    return file_handler


def get_logger(context='generic', pattern=''):
    logger = logging.getLogger(context)
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    os.makedirs('_logs', exist_ok=1)
    logger.addHandler(_file_handler(pattern=pattern))
    return logger


logger = get_logger(context='Trigger', pattern='trigger')
metric_logger = get_logger(context='Metric', pattern='metric')
