# -*- coding: utf-8 -*-
"""
Logic module for the stepper motor

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

import time

from qtpy import QtCore
import numpy as np

from qudi.util.mutex import RecursiveMutex
from qudi.core.connector import Connector
from qudi.core.module import LogicBase
from qudi.core.configoption import ConfigOption
from qudi.util.datastorage import TextDataStorage
from datetime import datetime
import matplotlib.pyplot as plt

class SpectrometerLogic(LogicBase):
    """ Logic module agreggating multiple hardware switches.
    """

    spectrometer = Connector(interface='OzySpectrometer')
    query_interval = ConfigOption('query_interval', 100)
    _poi_manager_logic = Connector(name='poi_manager_logic', interface='PoiManagerLogic')
    OPM = Connector(interface='OpmInterface')
    is_live = False
    integration_time=20000
    num_frames=0
    data=[]

    # signals
    sig_update_display = QtCore.Signal()
    sigStart = QtCore.Signal()
    sigStop = QtCore.Signal()
    sigSaveStateChanged = QtCore.Signal(bool)
    sigSingleShot = QtCore.Signal()


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.query_timer = QtCore.QTimer()
        self._thread_lock = RecursiveMutex()



    def on_activate(self):
        """ Prepare logic module for work.
        """

        self.stop_request = False
        self.buffer_length = 100
        self._spectrometer = self.spectrometer()
        self._poi = self._poi_manager_logic()
        self._opm = self.OPM()
        self.set_integration_time()
        self.wavelengths = self.get_wavelengths()
        self.intensities_counts = np.zeros(np.shape(self.wavelengths))
        self.isRunning = False

        self.sigStart.connect(self.start_query_loop)
        self.sigStop.connect(self.stop_query_loop)
        self.sigSingleShot.connect(self.singleShotAcquisition)

                # delay timer for querying hardware
        self.queryTimer = QtCore.QTimer()
        self.queryTimer.setInterval(self.query_interval)
        self.queryTimer.setSingleShot(True)
        self.queryTimer.timeout.connect(self.check_loop, QtCore.Qt.QueuedConnection)

        #QtCore.QTimer.singleShot(0, self.start_query_loop)



    def on_deactivate(self):
        """ When the module is deactivated
        """
        if self.is_live:
            self.stop_query_loop()
            for i in range(5):
                time.sleep(self.query_interval / 1000)
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
                self.queryTimer.start(self.query_interval)


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
        """ Get position and update display. """
        if self.stop_request:
            if self.module_state.can('stop'):
                self.module_state.stop()
            self.stop_request = False
            return
        qi = self.query_interval
        try:
            self.intensities_counts += self.get_intensities()
            self.num_frames+=1

        except:
            qi = 3000
            self.log.exception("Exception in spectrometer status loop, throttling refresh rate.")

        
        
        self.queryTimer.start(qi)
        self.sig_update_display.emit()

    @QtCore.Slot()
    def start_singleShotAcquisition(self):
        if not self.isRunning:
            self._opm.spectrometer_mode()
            self.sigSingleShot.emit()
            self.isRunning=True

    @QtCore.Slot()
    def singleShotAcquisition(self):
        try:
            self.isRunning=True
            self.intensities_counts=self.get_intensities()
            self.sig_update_display.emit()
        except:
            self.log.exception("Exception in spectrometer acquisition")
        self.isRunning=False


    def start_live_collection(self):
        # self.is_live = True

        # # delay timer for querying hardware
        # self.query_timer.setInterval(self.query_interval)
        # self.query_timer.setSingleShot(True)
        # self.query_timer.timeout.connect(self.check_loop, QtCore.Qt.QueuedConnection)

        # # self.start_query_loop()
        # QtCore.QTimer.singleShot(0, self.start_query_loop)
        if not self.isRunning:
            self._opm.spectrometer_mode()
            self.sigStart.emit()
            self.isRunning=True


    def stop_live_collection(self):
        """ Emits signal to stop query loop.
        """
        self.sigStop.emit()
        self._opm.camera_mode()
        self.isRunning = False
        self.sig_update_display.emit()


    def get_intensities(self):
        self.intensities_counts = self._spectrometer.get_intensities()

        self.sig_update_display.emit()
        return self.intensities_counts


    def get_wavelengths(self):
        return self._spectrometer.get_wave_lengths()


    def set_integration_time(self, int_time=20000):
        print(int_time/1E6)
        self.num_frames=0
        self.integration_time=int_time
        self._spectrometer.set_integration_time(int_time)


    def clear_data(self):
        self.num_frames=0
        self._spectrometer.clear()
        self.intensities_counts = np.zeros(np.shape(self.wavelengths))
        self.sig_update_display.emit()

    def initiate_save(self):
        print("Initating Save")
        self.save([self.wavelengths, self.intensities_counts])

    def plot_data(self, data, title=None):
        fig, ax = plt.subplots()
        ax.plot(data[0], data[1])
        ax.set_xlabel("Wavelength (nm)")
        ax.set_ylabel("Intensity (Arb.)")
        if title is not None:        # Y-axis label
            ax.set_title(title)  # Title
        else:
            ax.set_title("Spectrometer Measurement")
        return fig

    def save(self, scan_data):
        with self._thread_lock:
            if self.module_state() != 'idle':
                self.log.error('Unable to save Spectrometry Data. Saving still in progress...')
                return

            if scan_data is None:
                raise ValueError('Unable to save Spectrometry Data. No data available.')

            self.sigSaveStateChanged.emit(True)
            self.module_state.lock()
            try:
                ds = TextDataStorage(root_dir=self.module_default_data_dir)

                timestamp = datetime.now()
                # ToDo: Add meaningful metadata if missing:
                parameters = {}
                parameters["exposure_time"] = self.integration_time
                parameters["exposure_time_units"]="uSec"
                parameters["Number of Frames"] =  self.num_frames
                parameters["Wavelengths"] = "Wavelengths"
                parameters["Wavelength Units"] = "nm"
                parameters["Intensities"] = "Intensities"
                parameters["Intensity Units"] = "Arb."
                tag="Spectrum Measurement"

                if self._poi_manager_logic().active_POI_Visible():
                    parameters["ROI"]=self._poi_manager_logic().roi_name
                    parameters["POI"]=self._poi_manager_logic().active_poi
                    tag = "Spectrometry Scan of "+str(parameters["ROI"]+", "+str(parameters["POI"]))

                data=np.asarray(scan_data).transpose()
                file_path, _, _ = ds.save_data(data,
                                                   metadata=parameters,
                                                   nametag=tag,
                                                   timestamp=timestamp,
                                                   column_headers='Wavelength;;Intensity')
                    # thumbnail

                figure = self.plot_data(scan_data, tag)
                ds.save_thumbnail(figure, file_path=file_path.rsplit('.', 1)[0])

            finally:
                self.log.info("Spectrometry Data Saved at: " + str(file_path))
                self.module_state.unlock()
                self.sigSaveStateChanged.emit(False)
            return
