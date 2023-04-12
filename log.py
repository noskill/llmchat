import logging
import logging.handlers


def setupLogger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)

    f = logging.handlers.RotatingFileHandler('app.log')
    f.setFormatter(formatter)
    f.setLevel(logging.DEBUG)
    logger.addHandler(f)
