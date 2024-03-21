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
import pyfirmata

from qudi.util.mutex import RecursiveMutex
from qudi.core.connector import Connector
from qudi.core.module import LogicBase
from qudi.core.configoption import ConfigOption

class SpectrometerLogic(LogicBase):
    """ Logic module agreggating multiple hardware switches.
    """

    spec_meter = Connector(interface='OzySpectrometer')
    query_interval = ConfigOption('query_interval', 100)

    # signals
    sig_update_display = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thread_lock = RecursiveMutex()


    def on_activate(self):
        """ Prepare logic module for work.
        """
        self._spec_meter = self.spec_meter()
        self.set_integration_time()

        self.stop_request = False
        self.buffer_length = 100

        # delay timer for querying hardware
        self.query_timer = QtCore.QTimer()
        self.query_timer.setInterval(self.query_interval)
        self.query_timer.setSingleShot(True)
        self.query_timer.timeout.connect(self.check_loop, QtCore.Qt.QueuedConnection)

        # self.start_query_loop()
        QtCore.QTimer.singleShot(0, self.start_query_loop)


    def on_deactivate(self):
        """ When the module is deactivated
        """
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
                self.query_timer.start(self.query_interval)

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
                self.query_timer.stop()
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
            self.intensities += self.get_intensities()

        except:
            qi = 3000
            self.log.exception("Exception in stepper motor status loop, throttling refresh rate.")

        self.query_timer.start(qi)
        self.sig_update_display.emit()


    def get_intensities(self):
        """ Get the current coordinates

        Returns:
            tuple: (X, y)
        """
        return self._spec_meter.get_intensities()


    def set_integration_time(self, time=20000):
        self._spec_meter.set_integration_time(time)