from Logger.logger_interface import LoggerInterface


class DummyLogger(LoggerInterface):
    """A dummy logger that does nothing."""

    def debug(self, message: str):
        pass

    def info(self, message: str):
        pass

    def warning(self, message: str):
        pass

    def error(self, message: str):
        pass

    def critical(self, message: str):
        pass
