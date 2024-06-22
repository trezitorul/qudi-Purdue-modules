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

from qudi.util.mutex import RecursiveMutex
from qudi.core.configoption import ConfigOption
from qudi.core.connector import Connector
from qudi.core.module import LogicBase
from qtpy import QtCore


class QuTagLogic(LogicBase):
    """ Power meter logic module with query loop.
    """
    qutag = Connector(interface='Qutag')
    queryInterval = ConfigOption('query_interval', 100)

    # Signals

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
        ns=1e-9
        self._qutag.configG2(300, 1000,[5,6])
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
        print("HELLO")
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
        print("START")
        """ Emits signal to start query loop if not already running.
        """
        ns=1e-9
        self._qutag.configG2(300*ns, 1000,[5,6])
        if not self.isRunning:
            self.sigStart.emit()
            self.isRunning = True
        else:
            pass

    def stop(self):
        """ Emits signal to stop query loop.
        """
        self.sigStop.emit()
        self.isRunning = False