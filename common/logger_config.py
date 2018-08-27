import logging
import os
import sys
from common.util import print_time


def init_logger(name, filename):

    runtime_log_path = os.path.join('logs', 'runtime', filename)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(runtime_log_path, mode='w')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def error_msg(e):
    return  '{} on line {} at {}: {}'.format(type(e).__name__, sys.exc_info()[-1].tb_lineno, print_time(), e)