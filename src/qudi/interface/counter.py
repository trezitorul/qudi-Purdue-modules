from abc import abstractmethod
from qudi.core.module import Base

class Counter(Base):

    @abstractmethod
    def set_exposure_time(self, dt):
        """ A read-only data structure containing all hardware parameter limitations.
        """
        raise NotImplementedError # confused how this works if there is a NotImplementedError. could be that the methods that call the counter as a base actually go in and 
        # overwrite the method rather than it just being empty like this??
    
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