# -*- coding: utf-8 -*-
"""
Logic for APT piezo

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

from qudi.core.connector import Connector
from qudi.core.configoption import ConfigOption
from qudi.core.module import LogicBase
from qtpy import QtCore
from qudi.util.mutex import RecursiveMutex

class PIpiezoLogic(LogicBase):
    """ Logic module agreggating multiple hardware switches.
    """

    pi_piezo = Connector(interface='MotorInterface')
    query_interval = ConfigOption('query_interval', 100)

    position = [0.1,0.1,0.1]
    m=1
    um= m*1e-6

    # signals
    sig_update_display = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thread_lock = RecursiveMutex()

    def on_activate(self):
        """ Prepare logic module for work.
        """
        self._pi_stage = self.pi_piezo()
        self.stop_request = False
        self.buffer_length = 100

        # delay timer for querying hardware
        self.query_timer = QtCore.QTimer()
        self.query_timer.setInterval(self.query_interval)
        self.query_timer.setSingleShot(True)
        self.query_timer.timeout.connect(self.check_loop, QtCore.Qt.QueuedConnection)

        QtCore.QTimer.singleShot(0, self.start_query_loop)

    def on_deactivate(self):
        """ Deactivate modeule.
        """
        self.stop_query_loop()
        for i in range(5):
            time.sleep(self.query_interval / 1000)
            QtCore.QCoreApplication.processEvents()


    @QtCore.Slot()
    def start_query_loop(self):
        """ Start the readout loop. """
        if self.thread() is not QtCore.QThread.currentThread():
            QtCore.QMetaObject.invokeMethod(self,
                                            'start_query_loop',
                                            QtCore.Qt.BlockingQueuedConnection)
            return

        with self._thread_lock:
            if self.module_state() == 'idle':
                self.module_state.lock()
                self.query_timer.start(self.query_interval)

    # @QtCore.Slot()
    # def stop_query_loop(self):
    #     """ Stop the readout loop. """
    #     self.stop_request = True
    #     for i in range(10):
    #         if not self.stop_request:
    #             return
    #         QtCore.QCoreApplication.processEvents()
    #         time.sleep(self.query_interval/1000)

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
            self.position = self.get_position()

        except:
            qi = 3000
            self.log.exception("Exception in piezo status loop, throttling refresh rate.")

        self.query_timer.start(qi)
        self.sig_update_display.emit()

    def set_position(self, position=None,blocking=False):
        """
        Set the position of the piezo.
        ONLY WORKS IN CLOSED LOOP MODE
        Units: microns

        :param position: Output position relative to zero position; sets as an integer in the range 
                         from 0 to 32767, correspond to 0-100% of piezo extension aka maxTravel.
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """

        self._pi_stage.move_abs({'x':position[0]*self.um, 'y':position[1]*self.um, 'z':position[2]*self.um},blocking)


    def get_position(self , bay=0, channel=0, timeout=10):
        """
        Get position of the piezo as an integer in the range from 0 to 32767, correspond 
        to 0-100% of piezo extension aka maxTravel.
        Units: microns

        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        pos_dict = self._pi_stage.get_pos()
        position = [round(x,2) for x in [pos_dict['x']/self.um, pos_dict['y']/self.um, pos_dict['z']/self.um]]
        return position