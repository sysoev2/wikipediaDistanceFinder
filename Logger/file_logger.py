import logging

from Logger.logger_interface import LoggerInterface


class FileLogger(LoggerInterface):
    def __init__(self, file_name: str = 'log.txt'):
        self._logger = logging.getLogger("FileLogger")
        self._logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler(file_name)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        if not self._logger.handlers:
            self._logger.addHandler(file_handler)

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
