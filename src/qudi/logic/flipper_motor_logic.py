# -*- coding: utf-8 -*-
"""
Flipper mirror logic module.

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

from qtpy import QtCore
import pyfirmata

from qudi.util.mutex import RecursiveMutex
from qudi.core.connector import Connector
from qudi.core.module import LogicBase
from qudi.core.configoption import ConfigOption


class FlipperMotorLogic(LogicBase):
    """ Logic module for 2 flipper mirrors.
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
        # self.query_timer = QtCore.QTimer()
        # self.query_timer.setInterval(self.query_interval)
        # self.query_timer.setSingleShot(True)
        # self.query_timer.timeout.connect(self.check_loop, QtCore.Qt.QueuedConnection)

        # self.start_query_loop()
        # QtCore.QTimer.singleShot(0, self.start_query_loop)


    def on_deactivate(self):
        """ Deactivate modeule.
        """
        pass


    def set_mode(self, mode, num):
        """ Sets mode of flipper mirror of specified number 'num'.
        @param (str) mode: mode to set given mirror to; must be 'on' or 'off'
        @param (int) num: number of flipper mirror that will move; either 1 or 2
        """
        dir = 0
        if mode == 'on':
            dir = 1
        elif mode =='off':
            dir = -1
        else:
            self.log.error(f"Wrong mode input") 

        if num == 1:
            self._stepper_motor_1.move_rel(dir, 180)
        else:
            self._stepper_motor_2.SetMode(dir, 180)
