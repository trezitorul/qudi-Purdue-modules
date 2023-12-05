from abc import abstractmethod
from qudi.core.module import Base
class FlipperInterface(Base):
    """ Interface used to create a two state flipper such as the MF110 flipper motors from Thorlabs.  
    """
    @abstractmethod
    def on_activate(self):
        pass
    def on_deactivate(self):
        pass

    @abstractmethod
    def SetupDevice(self,deviceID):
        pass
    @abstractmethod
    def SetMode(self,mode):
        pass
    @abstractmethod
    def HomeMirror(self):
        pass