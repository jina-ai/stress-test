import os
import logging
from datetime import datetime


def _trigger_formatter():
    _datefmt = '%b %d %H:%M:%S'
    _fmt = '%(asctime)s | %(levelname)8s | %(processName)s | %(message)s'
    return logging.Formatter(fmt=_fmt, datefmt=_datefmt)


def _metrics_formatter():
    return logging.Formatter(fmt='%(message)s')


def _file_handler(context='trigger'):
    file_handler = logging.FileHandler(
        filename=datetime.now().strftime(f'_logs/{context}_%b_%d_%m_%Y.log'))
    file_handler.setFormatter(_trigger_formatter()) if context == 'trigger' \
        else file_handler.setFormatter(_metrics_formatter())
    return file_handler


def get_logger(context='trigger'):
    logger = logging.getLogger(context)
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    os.makedirs('_logs', exist_ok=1)
    logger.addHandler(_file_handler(context=context))
    return logger


logger = get_logger(context='trigger')
