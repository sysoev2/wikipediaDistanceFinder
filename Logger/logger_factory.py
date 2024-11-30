from Logger.console_logger import ConsoleLogger
from Logger.file_logger import FileLogger
from Logger.logger_interface import LoggerInterface


class LoggerFactory:
    @staticmethod
    def get_logger(logger_type: str) -> LoggerInterface:
        logger_type = logger_type.lower()
        if logger_type == "console":
            return ConsoleLogger()
        elif logger_type == "file":
            return FileLogger()
        else:
            raise ValueError(f"Unknown logger type: {logger_type}")
