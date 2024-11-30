from abc import ABC, abstractmethod


class LoggerInterface(ABC):
    """Abstract base class for loggers."""

    @abstractmethod
    def debug(self, message: str):
        pass

    @abstractmethod
    def info(self, message: str):
        pass

    @abstractmethod
    def warning(self, message: str):
        pass

    @abstractmethod
    def error(self, message: str):
        pass

    @abstractmethod
    def critical(self, message: str):
        pass