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

from qudi.core.configoption import ConfigOption
from qudi.core.connector import Connector
from qudi.core.module import LogicBase
from qtpy import QtCore


class FlipperMirrorLogic(LogicBase):
    """ Logic module for 2 flipper mirrors.
    """

    flipper1 = Connector(interface='FlipperMirror')
    flipper2 = Connector(interface='FlipperMirror')

    # signals
    sigUpdatePMDisplay = QtCore.Signal()

    # Connect signals

    def on_activate(self):
        """ Prepare logic module for work.
        """
        try:
            self._flipper1 = self.flipper1()
            self.log.info(f"Flipper 1 Connected")
            self._flipper1.HomeMirror()
        except Exception as e:
            self.log.warning(f"Flipper 1 failed to connect")

        try:
            self._flipper2 = self.flipper2()
            self.log.info(f"Flipper 2 Connected")
            self._flipper2.HomeMirror()
        except Exception as e:
            self.log.warning(f"Flipper 2 failed to connect")


    def on_deactivate(self):
        """ Deactivate modeule.
        """
        pass


    def set_mode(self, mode, num):
        """ Sets mode of flipper mirror of specified number 'num'.
        @param (str) mode: mode to set given mirror to; must be 'on' or 'off'
        @param (int) num: number of flipper mirror that will move; either 1 or 2
        """
        if num == 1:
            self._flipper1.SetMode(mode)
        else:
            self._flipper2.SetMode(mode)    
