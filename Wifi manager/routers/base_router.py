from abc import ABC, abstractmethod


class BaseRouter(ABC):

    @abstractmethod
    def login(self):
        pass

    @abstractmethod
    def get_devices(self):
        pass

    @abstractmethod
    def get_status(self):
        pass