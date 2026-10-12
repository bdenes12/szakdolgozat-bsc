import logging
import os

def setup_logger(name, level=logging.INFO, log_file='logs/app.log', console=True, file=True):

    logger = logging.getLogger(name)
    
    logger.setLevel(level)

    logger.handlers.clear()

    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    logFormatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    handlers = [h.name for h in logger.handlers]
    
    if console and "consoleHandler" not in handlers:
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        consoleHandler.set_name("consoleHandler")
        logger.addHandler(consoleHandler)

    if file and "fileHandler" not in handlers:
        fileHandler = logging.FileHandler(filename=log_file, encoding='utf-8')
        fileHandler.setFormatter(logFormatter)
        fileHandler.set_name("fileHandler")
        logger.addHandler(fileHandler)

    return logger
