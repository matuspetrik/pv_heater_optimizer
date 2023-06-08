from logging.handlers import RotatingFileHandler
from datetime import datetime
import logging
import yaml
from munch import Munch
from Lib.DataControl import FileHandler
import os

with FileHandler(os.environ['CONFIG_FILE'], "r") as cf:
    cfg = Munch(yaml.safe_load(cf))

path = cfg.log_file
maxLogFileSize = cfg.log_file_size
logger = logging.getLogger("Rotating Log")
logger.setLevel(logging.INFO)

# Add a rotating file handler
fileHandler = RotatingFileHandler(
                path,\
                maxBytes=maxLogFileSize,\
                backupCount=1
                )
fileHandler.setLevel(logging.DEBUG)
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)

def file(msg):
    logger.addHandler(fileHandler)
    logger.info(f'{datetime.now()}: {msg}')

def console(msg):
    logger.addHandler(consoleHandler)
    logger.info(f'{datetime.now()}: {msg}')