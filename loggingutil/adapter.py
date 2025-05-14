import logging
from loggingutil import LogLevel

class LoggingUtilHandler(logging.Handler):
    def __init__(self, logfile_instance):
        super().__init__()
        self.logfile = logfile_instance

    def emit(self, record):
        try:
            msg = self.format(record)
            level_map = {
                logging.INFO: LogLevel.INFO,
                logging.WARNING: LogLevel.WARN,
                logging.ERROR: LogLevel.ERROR,
                logging.CRITICAL: LogLevel.FATAL,
                logging.DEBUG: LogLevel.DEBUG
            }
            level = level_map.get(record.levelno, self.logfile.info)
            self.logfile.log(msg, level=level, tag=record.name)
        except Exception:
            self.handleError(record)
