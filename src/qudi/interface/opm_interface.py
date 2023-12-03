from abc import abstractmethod
from qudi.core.module import Base

class OpmInterface(Base):
    @abstractmethod
    def setup_scanning(self):
        pass

    @abstractmethod
    def shut_off(self):
        pass
    