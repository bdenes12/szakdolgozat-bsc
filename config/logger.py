import logging
import os
from logging.handlers import TimedRotatingFileHandler 

def setup_logger(name, level=logging.INFO, log_file='logs/app.log', console=True, file=True):

    logger = logging.getLogger(name)
    
    logger.setLevel(level)

    logger.handlers.clear()

    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    logFormatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    
    if console:
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        consoleHandler.set_name("consoleHandler")
        logger.addHandler(consoleHandler)

    if file:
        fileHandler = TimedRotatingFileHandler(filename=log_file, encoding='utf-8', when='midnight', interval=1, backupCount=10)
        fileHandler.setFormatter(logFormatter)
        fileHandler.set_name("fileHandler")
        fileHandler.namer = lambda name: name.replace(".log", "") + ".log"
        logger.addHandler(fileHandler)

    return logger
