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
    """ Power meter logic module with query loop.
    """
    qutag = Connector(interface='Qutag')
    _poi_manager_logic = Connector(name='poi_manager_logic', interface='PoiManagerLogic')
    queryInterval = ConfigOption('query_interval', 100)
    OPM = Connector(interface='OpmInterface')
    sigSaveStateChanged = QtCore.Signal(bool)

    g2Channels=[1,2]
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
        self._qutag.configG2(self.histWidth, self.binNum, self.g2Channels)
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

        QtCore.QTimer.singleShot(0, self.start_query_loop)
        

    def on_deactivate(self):
        """ Deactivate modeule.
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
        """ Get power and update display. """
        if self.stopRequest:
            if self.module_state.can('stop'):
                self.module_state.stop()
            self.stopRequest = False
            return
        qi = self.queryInterval
        try:
            
            self.time,self.counts = self.get_G2()
        except:
            qi = 3000
            self.log.exception("Exception in power meter status loop, throttling refresh rate.")

        self.queryTimer.start(qi)
        self.sig_update_display.emit()

    def get_G2(self):
        """ Retrieves output power in mW.
        @return (float): output ower in mW
        """
        return self._qutag.getG2()
    
    def start(self):
        """ Emits signal to start query loop if not already running.
        """
        ns=1e-9
        #self._qutag.configG2(30*ns, 1024,[5,6]) removed this line since it is set on activate, the G2 settings should be set via the GUI.
        if not self.isRunning:
            self._opm.g2_mode()
            self.sigStart.emit()
            self.isRunning = True
            self.log.info("G2 Acquisition Started")
            self.last_scan_start=datetime.now()
        else:
            pass

    def stop(self):
        """ Emits signal to stop query loop.
        """
        self._opm.camera_mode()
        self.sigStop.emit()
        self.isRunning = False
        self.log.info("G2 Acquisition Terminated")

    def reset(self):
        """Resets the g2 curve displayed, also initiates the stop. To start reacquiring start must be pressed.
        """
        self.log.info("G2 Histogram Reset")
        self.stop()
        self._qutag.resetG2()

    def updateG2Config(self, histWidth, binNum):
        if not self.isRunning:
            self.log.info("G2 Measurement configured with a histogram width of: " + str(histWidth) + "ns and " + str(binNum) + "Bins")
            self._qutag.configG2(histWidth, binNum,[1,2])
        else:
            self.log.warning("Can't set G2 Parameters during active measurement")

    def getHBTIntegrationTime(self):
        return self._qutag.getHBTIntegrationTime()
    
    def getHBTTotalCount(self):
        return self._qutag.getHBTTotalCount()
    
    def getHBTRate(self):
         return self._qutag.getHBTRate()
    
    def getHBTCount(self):
         return self._qutag.getHBTCount()
    
    def getHBTLiveInfo(self):
        return self._qutag.getHBTEventCount()
    def get_count_rates(self, channels):
        return self._qutag.get_count_rates(channels)
    
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
    
    def initiate_save(self):
        time, counts = self.get_G2()
        data=np.vstack((time,counts))
        self.save_g2(data)

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
                figure = self.plot_g2(scan_data, tag)
                ds.save_thumbnail(figure, file_path=file_path.rsplit('.', 1)[0])
            finally:
                self.log.info("G2(t) Saved at: " + str(file_path))
                self.module_state.unlock()
                self.sigSaveStateChanged.emit(False)
            return