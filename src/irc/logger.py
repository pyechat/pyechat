import logging

from src.irc.json_formatter import JsonFormatter


class Logger:
    def __init__(self):
        json_formatter = JsonFormatter({"level": "levelname",
                                        "message": "message",
                                        "loggerName": "name",
                                        "processName": "processName",
                                        "processID": "process",
                                        "threadName": "threadName",
                                        "threadID": "thread",
                                        "timestamp": "asctime"})
        logging.Formatter(json_formatter)

    def log(self, level, message):
        if level.lower() == 'debug':
            logging.debug(message)
        elif level.lower() == 'info':
            logging.info(message)
        elif level.lower() == 'warning':
            logging.warning(message)
        elif level.lower() == 'error':
            logging.error(message)
