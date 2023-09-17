#-*- coding: utf-8 -*-
"""
Laser management.

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
import numpy as np
from qtpy import QtCore

from qudi.core.connector import Connector
from qudi.core.module import LogicBase

class LtuneLaserLogic(LogicBase):

    purdue_laser = Connector(interface='LtuneLaser')
    
    # queryInterval = ConfigOption('query_interval', 100)
    sig_update_laser_display = QtCore.Signal()

    def on_activate(self):
        """Activate the module
        """
        self._laser = self.purdue_laser()

    
    def on_deactivate(self):
        """Deactivate the module
        """
        self.disable_laser()

    def enable_laser(self):
        """ Enable the laser
        """
        self._laser.enable()

    def disable_laser(self):
        """Disable the laser
        """
        self._laser.disable()


    def set_power(self, power):
        """Set the power of the laser

        Args:
            power (float): Power of the laser
        """
        self._laser.set_output_power(power)
        self.power = self._laser.power
        self.sig_update_laser_display.emit()


    def get_power(self):
        """Get the current power

        Returns:
            float: current power
        """
        return self._laser.get_output_power()

