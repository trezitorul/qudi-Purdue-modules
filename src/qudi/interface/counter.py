from abc import abstractmethod
from qudi.core.module import Base

class Counter(Base):

    @abstractmethod
    def set_exposure_time(self, dt):
        """ A read-only data structure containing all hardware parameter limitations.
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_exposure_time(self, dt):
        """ A read-only data structure containing all hardware parameter limitations.
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_counts(self, channels):
        """ A read-only data structure containing all hardware parameter limitations.
        """
        raise NotImplementedError

    @abstractmethod
    def get_count_rates(self, channels):
        """ A read-only data structure containing all hardware parameter limitations.
        """
        raise NotImplementedError