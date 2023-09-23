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

import numpy as np
import time

from qudi.core.connector import Connector
from qudi.core.configoption import ConfigOption
from qudi.logic.generic_logic import GenericLogic
from qtpy import QtCore


class APTpiezoLogic(GenericLogic):
    """ Logic module agreggating multiple hardware switches.
    """

    apt_piezo_1 = Connector(interface='ConfocalDevInterface')
    apt_piezo_2 = Connector(interface='ConfocalDevInterface')
    query_interval = ConfigOption('query_interval', 100)

    position = [0,0,0]
    m=1
    um= m*1e-6

    # signals
    sig_update_display = QtCore.Signal()

    def on_activate(self):
        """ Prepare logic module for work.
        """
        self._aptpiezo_1 = self.apt_piezo_1()
        self._aptpiezo_2 = self.apt_piezo_2()
        self.stop_request = False
        self.buffer_length = 100

        # delay timer for querying hardware
        self.query_timer = QtCore.QTimer()
        self.query_timer.setInterval(self.query_interval)
        self.query_timer.setSingleShot(True)
        self.query_timer.timeout.connect(self.check_loop, QtCore.Qt.QueuedConnection)

        self.start_query_loop()

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
        #self.module_state.run()
        self.query_timer.start(self.query_interval)

    @QtCore.Slot()
    def stop_query_loop(self):
        """ Stop the readout loop. """
        self.stop_request = True
        for i in range(10):
            if not self.stop_request:
                return
            QtCore.QCoreApplication.processEvents()
            time.sleep(self.query_interval/1000)
    
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

    def set_position(self, position=None):
        """
        Set the position of the piezo.
        ONLY WORKS IN CLOSED LOOP MODE
        Units: microns

        :param position: Output position relative to zero position; sets as an integer in the range 
                         from 0 to 32767, correspond to 0-100% of piezo extension aka maxTravel.
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
    
        self._aptpiezo_1.set_position(position=position[0], channel=0)
        self._aptpiezo_1.set_position(position=position[1], channel=1)
        self._aptpiezo_2.set_position(position=position[2], channel=0)


    def get_position(self , bay=0, channel=0, timeout=10):
        """
        Get position of the piezo as an integer in the range from 0 to 32767, correspond 
        to 0-100% of piezo extension aka maxTravel.
        Units: microns

        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """

        position = [self._aptpiezo_1.get_position(channel=0), self._aptpiezo_1.get_position(channel=1), self._aptpiezo_2.get_position(channel=0)]
        return position