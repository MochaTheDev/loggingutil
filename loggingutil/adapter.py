import logging

class LoggingUtilHandler(logging.Handler):
    def __init__(self, logfile_instance):
        super().__init__()
        self.logfile = logfile_instance

    def emit(self, record):
        try:
            msg = self.format(record)
            level_map = {
                logging.INFO: self.logfile.info,
                logging.WARNING: self.logfile.warn,
                logging.ERROR: self.logfile.error,
                logging.CRITICAL: self.logfile.fatal,
                logging.DEBUG: self.logfile.debug
            }
            level = level_map.get(record.levelno, self.logfile.info)
            self.logfile.log(msg, level=level, tag=record.name)
        except Exception:
            self.handleError(record)
