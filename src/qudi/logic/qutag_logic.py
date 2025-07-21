# -*- coding: utf-8 -*-
"""
Powermeter logic module that queries the hardware.

Qudi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Qudi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Qudi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at <https://github.com/Ulm-IQO/qudi/>
"""

import numpy as np
import time
from datetime import datetime
import matplotlib.pyplot as plt

from qudi.util.mutex import RecursiveMutex
from qudi.core.configoption import ConfigOption
from qudi.core.connector import Connector
from qudi.core.module import LogicBase
from qtpy import QtCore
from qudi.util.datastorage import TextDataStorage

class QuTagLogic(LogicBase):
    """ Qutag Logic Module, this modules handles the logic for the time tagger hardware, it accesses the count rate, the lifetime,and G2 measurement capabilities of the Qutag.
    """
    qutag = Connector(interface='Qutag')
    _poi_manager_logic = Connector(name='poi_manager_logic', interface='PoiManagerLogic')
    queryInterval = ConfigOption('query_interval', 100)
    g2_channels = ConfigOption(name="g2_channels", missing="error")
    lifetime_channels = ConfigOption(name="lifetime_channels", missing="error") #A list of channels to use for the lifetime measurements index 0 is the start channel index 1 - n are all the channels the lifetime is measured on.
    lifetime_delays = ConfigOption(name="lifetime_delays", missing="error") #ps, default value is 140 ps
    OPM = Connector(interface='OpmInterface')
    sigSaveStateChanged = QtCore.Signal(bool)

    measurement_type = None #Should be "G2" or "LIFETIME" for the measurement type in progress

    histWidth=30
    binNum=1024
    # Signals
    last_scan_start = None

    sig_update_display = QtCore.Signal()
    sigStart = QtCore.Signal()
    sigStop = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thread_lock = RecursiveMutex()


    def on_activate(self):
        """ Prepare logic module for work.
        """
        self._qutag = self.qutag()
        self._opm = self.OPM()
        self._poi = self._poi_manager_logic()
        ns=1e-9
        self._qutag.configG2(self.histWidth, self.binNum, self.g2_channels)
        self._qutag.configLifetime(self.histWidth, self.binNum, self.lifetime_channels, self.lifetime_delays)
        self.stopRequest = False
        self.bufferLength = 100

        self.counts = 0
        self.time=0
        self.isRunning = False

        # Connect signals
        self.sigStart.connect(self.start_query_loop)
        self.sigStop.connect(self.stop_query_loop)

        # delay timer for querying hardware
        self.queryTimer = QtCore.QTimer()
        self.queryTimer.setInterval(self.queryInterval)
        self.queryTimer.setSingleShot(True)
        self.queryTimer.timeout.connect(self.check_loop, QtCore.Qt.QueuedConnection)

        #QtCore.QTimer.singleShot(0, self.start_query_loop)

    def on_deactivate(self):
        """ Deactivate module.
        """
        self.stop_query_loop()
        for i in range(5):
            time.sleep(self.queryInterval / 1000)
            QtCore.QCoreApplication.processEvents()

    @QtCore.Slot()
    def start_query_loop(self):
        """ Start the readout loop. """
        # self.query_timer.start(self.query_interval)

        if self.thread() is not QtCore.QThread.currentThread():
            QtCore.QMetaObject.invokeMethod(self,
                                            'start_query_loop',
                                            QtCore.Qt.BlockingQueuedConnection)
            return

        with self._thread_lock:
            if self.module_state() == 'idle':
                self.module_state.lock()
                self.queryTimer.start(self.queryInterval)

    @QtCore.Slot()
    def stop_query_loop(self):
        """ Stop the readout loop. """
        if self.thread() is not QtCore.QThread.currentThread():
            QtCore.QMetaObject.invokeMethod(self,
                                            'stop_query_loop',
                                            QtCore.Qt.BlockingQueuedConnection)
            return

        with self._thread_lock:
            if self.module_state() == 'locked':
                self.queryTimer.stop()
                self.module_state.unlock()

    @QtCore.Slot()
    def check_loop(self):
        """ Get measurement histogram and emit signal to update display in the GUI. """
        if self.stopRequest:
            if self.module_state.can('stop'):
                self.module_state.stop()
            self.stopRequest = False
            return
        qi = self.queryInterval
        try:
            if self.measurement_type == "G2":
                self.time, self.counts = self.get_G2()
            elif self.measurement_type == "LIFETIME":
                self.time, self.counts = self.get_Lifetime()
        except:
            qi = 3000
            self.log.exception("Exception in status loop, throttling refresh rate.")

        self.queryTimer.start(qi)
        self.sig_update_display.emit()

    def get_G2(self):
        """ Returns the G2 histogram from the Qutag.
        Args:
            None
        Returns:
            list: [numpy list of bins, numpy list of counts in each bin]
        """
        return self._qutag.getG2()
    
    def get_Lifetime(self):
        """ Returns the Lifetime histogram from the Qutag.
        Args:
            None
        Returns:
            list: [numpy list of bins, numpy list of counts in each bin]
        """
        return self._qutag.getLifetime()
        
    def start(self, measurement_type):
        """ Emits signal to start query loop if not already running.
        Args:
            measurement_type (str): Type of measurement to start, either "G2" or "LIFETIME".

        Returns:
            None
        """
        ns=1e-9
        #self._qutag.configG2(30*ns, 1024,[5,6]) removed this line since it is set on activate, the G2 settings should be set via the GUI.
        if not self.isRunning:
            self._opm.g2_mode()
            self.sigStart.emit()
            self.isRunning = True
            self.measurement_type = measurement_type
            self.log.info(str(measurement_type) + " Acquisition Started")
            self.last_scan_start=datetime.now()
        else:
            pass

    def stop(self):
        """ Emits signal to stop query loop.
        """
        self._opm.camera_mode()
        self.sigStop.emit()
        self.isRunning = False
        self.log.info("Qutag Acquisition Terminated")

    def reset(self):
        """Resets the G2 and Lifetime Histograms curve displayed, also initiates the stop. To start reacquiring start must be pressed.
        """
        self.log.info("Lifetime and G2 Histogram Reset")
        self.stop()
        self._qutag.resetG2()
        self._qutag.resetLFT()


    def updateConfig(self, histWidth, binNum):
        """ Update the configuration for the G2 or Lifetime measurement. This has a switch allowing for context dependent configuration depending on the measurement mode.
        Args:
            histWidth (int): Width of the histogram in nanoseconds.
            binNum (int): Number of bins in the histogram.
        Returns:
            None
        """
        if self.measurement_type == "G2":
            self.updateG2Config(histWidth, binNum)
        elif self.measurement_type == "LIFETIME":
            self.updateLifetimeConfig(histWidth, binNum)

    def updateG2Config(self, histWidth, binNum):
        """ Update the configuration for the G2 measurement.
        Args:
            histWidth (int): Width of the histogram in nanoseconds.
            binNum (int): Number of bins in the histogram.
        Returns:
            None
        """
        if not self.isRunning:
            self.log.info("G2 Measurement configured with a histogram width of: " + str(histWidth) + "ns and " + str(binNum) + "Bins")
            self._qutag.configG2(histWidth, binNum,self.g2_channels)
        else:
            self.log.warning("Can't set G2 Parameters during active measurement")

    def updateLifetimeConfig(self, histWidth, binNum):
        """ Update the configuration for the G2 measurement.
        Args:
            histWidth (int): Width of the histogram in nanoseconds.
            binNum (int): Number of bins in the histogram.
        Returns:
            None
        """
        if not self.isRunning:
            self.log.info("Lifetime Measurement Configured with a Histogram Width of: " + str(histWidth) + "ns and " + str(binNum) + "Bins")
            self._qutag.configLifetime(histWidth, binNum, self.lifetime_channels, self.lifetime_delays)
        else:
            self.log.warning("Can't set Lifetime Parameters during active measurement")

    def getHBTIntegrationTime(self):
        """ Returns the integration time for the HBT measurement.
        Args:
            None
        Returns:
            double: Integration time in seconds.
        """
        return self._qutag.getHBTIntegrationTime()
    
    def getLFTIntegrationTime(self):
        """ Returns the integration time for the Lifetime measurement.
        Args:
            None
        Returns:
            double: Integration time in seconds.
        """
        return self._qutag.getLFTExposureTime()
    
    def getLFTStartEvents(self):
        """ Returns the number of start events for the current lifetime histogram. 
        Typically this is the number of sync pulses received by the time tagger from the pulsed laser source.
        Args:
            None
        Returns:
            int: Number of times the start channel was triggered.
        """
        return self._qutag.getLFTStartEvents()
    
    def getLFTStopEvents(self):
        """ Returns the number of stop events for the current lifetime histogram. 
        Typically this is the number of times the time tagger was triggered by the stop channel, which is usually the detector channel.
        Args:
            None
        Returns:
            int: Number of times the stop channel was triggered.
        """
        return self._qutag.getLFTStopEvents()
    
    def getHBTTotalCount(self):
        """ Returns the total number of times the channels contributing to the HBT histogram were triggered.
        Args:
            None
        Returns:
            int: Total number of counts for both channels.
        """
        return self._qutag.getHBTTotalCount()
    
    def getHBTRate(self):
        """ Returns the rate of counts for each channel contributing to the HBT histogram.
        Args:
            None
        Returns:
            list: List of rates for each detector channel, usually two channels for a standard G2 measurement.
        """
        return self._qutag.getHBTRate()
    
    def getHBTCount(self):
         return self._qutag.getHBTCount()
    
    def getHBTLiveInfo(self):
        return self._qutag.getHBTEventCount()
    
    def getLFTLiveInfo(self):
        return self._qutag.getLFTStats()
    
    def get_count_rates(self, channels):
        return self._qutag.get_count_rates(channels)

    def plot(self, data, title=None):
        if self.measurement_type == "G2":
            return self.plot_g2(data, title)
        elif self.measurement_type == "LIFETIME":
            return self.plot_lifetime(data, title)
    
    def plot_g2(self,data, title=None):
        fig, ax = plt.subplots()
        ax.plot(*data)
        ax.set_xlabel('Time (ns)')      # X-axis label
        ax.set_ylabel('g2(t)')  
        if title is not None:        # Y-axis label
            ax.set_title(title)  # Title
        else:
            ax.set_title("g2(t)")
        return fig
    
    def plot_lifetime(self, data, title=None):
        fig, ax = plt.subplots()
        ax.plot(*data)
        ax.set_xlabel('Time (ns)')      # X-axis label
        ax.set_ylabel('g2(t)')  
        if title is not None:        # Y-axis label
            ax.set_title(title)  # Title
        else:
            ax.set_title("g2(t)")
        return fig       
    
    @QtCore.Slot() 
    def initiate_save(self):
        """ Initiates the save process for the current measurement.
        """
        if self.measurement_type == "G2":
            self.initiate_g2_save()
        elif self.measurement_type == "LIFETIME":
            self.initiate_lifetime_save()

    @QtCore.Slot() 
    def initiate_g2_save(self):
        time, counts = self.get_G2()
        data=np.vstack((time,counts))
        self.save_g2(data)

    @QtCore.Slot() 
    def initiate_lifetime_save(self):
        time, counts = self.get_Lifetime()
        data=np.vstack((time,counts))
        self.save_lifetime(data)
    
    def save(self, scan_data):
        """ Save the current scan data.
        """
        if self.measurement_type == "G2":
            self.save_g2(scan_data)
        elif self.measurement_type == "LIFETIME":
            self.save_lifetime(scan_data)

    

    def save_lifetime(self, scan_data):
        print("Attempting to Save Lifetime")
        with self._thread_lock:
            if self.module_state() != 'idle':
                self.log.error('Unable to save Lifetime Measurment. Saving still in progress...')
                return

            if scan_data is None:
                raise ValueError('Unable to save Lifetime Measurement. No data available.')

            self.sigSaveStateChanged.emit(True)
            self.module_state.lock()
            try:
                ds = TextDataStorage(root_dir=self.module_default_data_dir)

                timestamp = datetime.now()
                # ToDo: Add meaningful metadata if missing:
                parameters = {}
                print("1")
                parameters["bin_size"] = self._qutag.getLFTBinWidth()
                print("2")
                parameters["bin_count"] = self._qutag.getLFTBinCount()
                print("3")
                parameters["total exposure time"] = self._qutag.getLFTExposureTime() #Check to see how this retrieves the current dataset to make sure it is synced.
                print("4")
                parameters['measurement start'] = self.last_scan_start
                parameters["y-axis name"] = "Normalized Counts"
                parameters["y-axis Units"] = "Arb. Units"
                parameters["x-axis name"] = "Time"
                parameters["x-axis units"] = "S"
                print("test")

                # will have to append experiment name to tag ideally
                # notes will just be added metadata
                tag="Lifetime Measurement"
                print(self._poi_manager_logic().active_POI_Visible())
                if self._poi_manager_logic().active_POI_Visible():
                    parameters["ROI"]=self._poi_manager_logic().roi_name
                    parameters["POI"]=self._poi_manager_logic().active_poi
                    tag = "Lifetime  of "+str(parameters["ROI"]+", "+str(parameters["POI"]))
                file_path, _, _ = ds.save_data(scan_data,
                                                   metadata=parameters,
                                                   nametag=tag,
                                                   timestamp=timestamp,
                                                   column_headers='Time(S);;Normalized Lifetime Counts (I. Arb)')
                    # thumbnail
                figure = self.plot(scan_data, tag)
                ds.save_thumbnail(figure, file_path=file_path.rsplit('.', 1)[0])
            finally:
                self.log.info("Lifetime Saved at: " + str(file_path))
                self.module_state.unlock()
                self.sigSaveStateChanged.emit(False)
            return

    def save_g2(self, scan_data):
        print("Attempting to Save G2")
        with self._thread_lock:
            if self.module_state() != 'idle':
                self.log.error('Unable to save G2 Measurment. Saving still in progress...')
                return

            if scan_data is None:
                raise ValueError('Unable to save G2 Measurement. No data available.')

            self.sigSaveStateChanged.emit(True)
            self.module_state.lock()
            try:
                ds = TextDataStorage(root_dir=self.module_default_data_dir)

                timestamp = datetime.now()
                # ToDo: Add meaningful metadata if missing:
                parameters = {}
                parameters["bin_size"] = self._qutag.getHBTBinWidth()
                parameters["bin_count"] = self._qutag.getHBTBinCount()
                parameters["total events"] = self._qutag.getHBTTotalCount()
                parameters['measurement start'] = self.last_scan_start
                parameters["y-axis name"] = "Normalized Counts"
                parameters["y-axis Units"] = "Arb. Units"
                parameters["x-axis name"] = "Time"
                parameters["x-axis units"] = "S"
                tag="G2(t) Scan"
                print(self._poi_manager_logic().active_POI_Visible())
                if self._poi_manager_logic().active_POI_Visible():
                    parameters["ROI"]=self._poi_manager_logic().roi_name
                    parameters["POI"]=self._poi_manager_logic().active_poi
                    tag = "G2(t) Scan of "+str(parameters["ROI"]+", "+str(parameters["POI"]))
                file_path, _, _ = ds.save_data(scan_data,
                                                   metadata=parameters,
                                                   nametag=tag,
                                                   timestamp=timestamp,
                                                   column_headers='Time(S);;Normalized G2 Counts (I. Arb)')
                    # thumbnail
                figure = self.plot(scan_data, tag)
                ds.save_thumbnail(figure, file_path=file_path.rsplit('.', 1)[0])
            finally:
                self.log.info("G2(t) Saved at: " + str(file_path))
                self.module_state.unlock()
                self.sigSaveStateChanged.emit(False)
            return