# -*- coding: utf-8 -*-
""" Logic module for the DAQ counter
"""

import time
from qudi.util.mutex import RecursiveMutex
from qudi.core.configoption import ConfigOption
from qudi.core.connector import Connector
from qudi.core.module import LogicBase
from qudi.util.datastorage import TextDataStorage
import time
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

# from logic.generic_logic import GenericLogic

from qtpy import QtCore


class polarization_measurement_logic(LogicBase):
    """ Logic module to interface with multichannel counting hardware.
    """
    #counter_channels = ConfigOption(name='counter_channels', missing='error')#Dictionary with channel info and channel name.
    int_time = ConfigOption("IntegrationTime", 0.1)#Sets the default integration time per angle to 100ms
    counter = Connector(interface='counter_logic')
  #  pol_motor = Connector(interface='PolarMotorLogic')
    _poi_manager_logic = Connector(name='poi_manager_logic', interface='PoiManagerLogic')
    #query_interval = ConfigOption('query_interval', 100) #How often to update the display
    data = [[],[]] #Nexted list, first list of elements are the scan angles used, and the second are the counter values at that angle.
    scan_angles =[] #Angles to be scanned on current scan

    
    # signals
    sig_update_display = QtCore.Signal()
    sigSaveStateChanged = QtCore.Signal(bool)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thread_lock = RecursiveMutex()

    def on_activate(self):
        """ Prepare logic module for work.
        """
        self._counter = self.counter()
        self.counter_channels = self._counter.get_counter_channels()
        self._poi = self._poi_manager_logic()

        self.stop_request = False
        self.buffer_length = 100
        self.set_exposure_time(self.int_time)
        
#        self._pol_motor = self.pol_motor()

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
        self.scan_angles=angles

    #@QtCore.Slot()
    def start_measurement_loop(self):
        self.log.info("Starting Polarization Scan: " + self.scan_angles)
        """ Start the readout loop. """
        self.last_scan_start=datetime.now()
        self.data = []
        # self.query_timer.start(self.query_interval)
        self._counter.set_exposure_time(self.int_time)
        for angle in self.scan_angles:        
            print("Setting Angle:" + str(angle))    
            #self._pol_motor.set_position(angle)
            print("Angle Set")
            #counts=self._counter.get_counts(self.counter_channels)
            counts = angle

            print("Measured Angle: " + str(angle) + "Measured Counts:" + str(counts))
            self.data.append([angle, counts])
            self.sig_update_display.emit()
            #time.sleep(1)

    def set_exposure_time(self,dt):
        self.int_time = dt
        self._counter.set_exposure_time(self.int_time)

    def get_exposure_time(self):
        self.dt=self._counter.get_exposure_time()
        return self.dt
    
    def initiate_save(self):
        print("Initating Save")
        self.save(self.data)

    def plot_data(self, data, title=None):
        fig, ax = plt.subplots(subplot_kw={"projection":"polar"})
        theta = np.deg2rad(np.vstack(data)[0])
        r = np.vstack(data)[1]
        ax.plot([theta, r], label="Counts")
        ax.legend()
        if title is not None:        # Y-axis label
            ax.set_title(title)  # Title
        else:
            ax.set_title("Excitation Polarization Measurement")
        return fig

    def save(self, scan_data):
        print("Attempting to Save Excitation Polarization Data")
        with self._thread_lock:
            if self.module_state() != 'idle':
                self.log.error('Unable to save Excitation Polarization Measurment. Saving still in progress...')
                return

            if scan_data is None:
                raise ValueError('Unable to save Excitation Polarization Measurement. No data available.')

            self.sigSaveStateChanged.emit(True)
            self.module_state.lock()
            try:
                ds = TextDataStorage(root_dir=self.module_default_data_dir)

                timestamp = datetime.now()
                # ToDo: Add meaningful metadata if missing:
                parameters = {}
                parameters["exposure_time"] = self.get_exposure_time()
                parameters['measurement start'] = self.last_scan_start
                parameters["r-axis name"] = "Counts"
                parameters["r-axis Units"] = "Counts"
                parameters["theta-axis name"] = "Angle"
                parameters["theta-axis units"] = "Degrees"
                tag="Excitation Polarization Measurement"
                print(self._poi_manager_logic().active_POI_Visible())
                if self._poi_manager_logic().active_POI_Visible():
                    parameters["ROI"]=self._poi_manager_logic().roi_name
                    parameters["POI"]=self._poi_manager_logic().active_poi
                    tag = "Excitation Polarization Scan of "+str(parameters["ROI"]+", "+str(parameters["POI"]))
                print(scan_data)
                file_path, _, _ = ds.save_data(scan_data,
                                                   metadata=parameters,
                                                   nametag=tag,
                                                   timestamp=timestamp,
                                                   column_headers='theta;;r')
                    # thumbnail
                figure = self.plot_data(scan_data, tag)
                ds.save_thumbnail(figure, file_path=file_path.rsplit('.', 1)[0])
            finally:
                self.log.info("Excitation Polarization Data Saved at: " + str(file_path))
                self.module_state.unlock()
                self.sigSaveStateChanged.emit(False)
            return