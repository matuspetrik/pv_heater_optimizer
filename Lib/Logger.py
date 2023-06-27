from logging.handlers import RotatingFileHandler
from datetime import datetime
import logging
import yaml
from munch import Munch
from Lib.DataControl import FileHandler
from Lib.DataControl import parseConfig
import os

cfgFile = parseConfig(fileOnly=True)
with FileHandler(cfgFile, "r") as cf:
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