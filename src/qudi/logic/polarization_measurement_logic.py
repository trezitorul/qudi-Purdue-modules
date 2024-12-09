# -*- coding: utf-8 -*-
""" Logic module for the DAQ counter
"""

import time
from qudi.util.mutex import RecursiveMutex
from qudi.core.configoption import ConfigOption
from qudi.core.connector import Connector
from qudi.core.module import LogicBase
import time

# from logic.generic_logic import GenericLogic

from qtpy import QtCore


class polarization_measurement_logic(LogicBase):
    """ Logic module to interface with multichannel counting hardware.
    """
    #counter_channels = ConfigOption(name='counter_channels', missing='error')#Dictionary with channel info and channel name.
    int_time = ConfigOption("IntegrationTime", 0.1)#Sets the default integration time per angle to 100ms
    counter = Connector(interface='counter_logic')
    pol_motor = Connector(interface='PolarMotorLogic')
    #query_interval = ConfigOption('query_interval', 100) #How often to update the display
    data = [[],[]] #Nexted list, first list of elements are the scan angles used, and the second are the counter values at that angle.
    scan_angles =[] #Angles to be scanned on current scan

    
    # signals
    sig_update_display = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thread_lock = RecursiveMutex()

    def on_activate(self):
        """ Prepare logic module for work.
        """
        self._counter = self.counter()
        self.counter_channels = self._counter.get_counter_channels()

        self.stop_request = False
        self.buffer_length = 100
        self.set_exposure_time(self.int_time)
        
        self._pol_motor = self.pol_motor()

        # delay timer for querying hardware
        #self.query_timer = QtCore.QTimer()
        #self.query_timer.setInterval(self.query_interval)
        #self.query_timer.setSingleShot(True)
        #self.query_timer.timeout.connect(self.check_loop, QtCore.Qt.QueuedConnection)

        #QtCore.QTimer.singleShot(0, self.start_query_loop)

    def on_deactivate(self):
        """ When the module is deactivated
        """
        pass
        #self.stop_query_loop()
        #for i in range(5):
            #time.sleep(self.query_interval / 1000)
            #QtCore.QCoreApplication.processEvents()

    def set_scan_parameters(self, int_time, angles): 
        """Sets the parameters for a scan
            int_time: The integration time in seconds
            angles: A list of angles in degrees to be measured
        """
        self.counter.set_exposure_time(self, int_time)

    @QtCore.Slot()
    def start_measurement_loop(self):
        """ Start the readout loop. """
        # self.query_timer.start(self.query_interval)
        self._counter.set_exposure_time(self.int_time)
        for angle in self.scan_angles:        
            print("Setting Angle:" + str(angle))    
            self._pol_motor.set_position(angle)
            print("Angle Set")
            #counts=self._counter.get_counts(self.counter_channels)
            counts = angle
            print("Measured Angle: " + str(angle) + str(counts))
            self.data.append((angle, counts))
            self.sig_update_display.emit()


    def set_exposure_time(self,dt):
        self.int_time = dt
        self._counter.set_exposure_time(self.int_time)

    def get_exposure_time(self):
        self.dt=self._counter.get_exposure_time()
        return self._counter.get_exposure_time()
    
    