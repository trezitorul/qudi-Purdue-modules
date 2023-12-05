from abc import abstractmethod
from qudi.core.module import Base

class OpmInterface(Base):
    @abstractmethod
    def on_activate(self):
        pass

    @abstractmethod
    def on_deactivate(self):
        pass
    
    
    