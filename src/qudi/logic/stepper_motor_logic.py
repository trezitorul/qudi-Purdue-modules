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

class StepperMotorLogic(LogicBase):
    """ Logic module agreggating multiple hardware switches.
    """

    stepper_motor_1 = Connector(interface='StepperMotor')
    stepper_motor_2 = Connector(interface='StepperMotor')
    com_port = ConfigOption(name='com_port', missing='error')
    query_interval = ConfigOption('query_interval', 100)

    # signals
    sig_update_display = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thread_lock = RecursiveMutex()


    def on_activate(self):
        """ Prepare logic module for work.
        """
        self.board = pyfirmata.Arduino(self.com_port)
        self._stepper_motor_1 = self.stepper_motor_1()
        self._stepper_motor_2 = self.stepper_motor_2()

        self._stepper_motor_1.initialize(self.board)
        self._stepper_motor_2.initialize(self.board)
        self.stop_request = False
        self.position = (0, 0)
        self.rpm = 12

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
        # self.stop_request = True
        # for i in range(10):
        #     if not self.stop_request:
        #         return
        #     QtCore.QCoreApplication.processEvents()
        #     time.sleep(self.query_interval/1000)
        # self.query_timer.stop()

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
            self.log.exception("Exception in stepper motor status loop, throttling refresh rate.")

        self.query_timer.start(qi)
        self.sig_update_display.emit()


    def move_rel(self, axis, direction, step=1):
        """Move the motor relatively

        Args:
            axis (int): 01 corresponds to xy
            direction (int): -1 corresponds to up/right; 1 corresponds to down/left
            step (int, optional): numeber of steps. Defaults to 1.
        """
        if (axis == 0): self._stepper_motor_1.move_rel(direction, step)
        if (axis == 1): self._stepper_motor_2.move_rel(direction, step)


    def get_position(self):
        """ Get the current coordinates

        Returns:
            tuple: (X, y)
        """
        positionX = self._stepper_motor_1.get_pos()
        positionY = self._stepper_motor_2.get_pos()
        return (positionX, positionY)


    def set_rpm(self, rpm):
        """Set the rpm

        Args:
            rpm (float): round-per-minute
        """
        self._stepper_motor_1.set_rpm(rpm)
        self._stepper_motor_2.set_rpm(rpm)
        self.rpm = rpm
