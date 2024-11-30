import logging

from Logger.logger_interface import LoggerInterface


class ConsoleLogger(LoggerInterface):
    def __init__(self):
        self._logger = logging.getLogger("ConsoleLogger")
        self._logger.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)

        if not self._logger.handlers:
            self._logger.addHandler(console_handler)

    def debug(self, message: str):
        self._logger.debug(message)

    def info(self, message: str):
        self._logger.info(message)

    def warning(self, message: str):
        self._logger.warning(message)

    def error(self, message: str):
        self._logger.error(message)

    def critical(self, message: str):
        self._logger.critical(message)

