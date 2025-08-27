# -*- coding: utf-8 -*-

"""
This file contains a gui for manual LAC control.

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

import os
import numpy as np

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from qtpy import uic
from qudi.util.colordefs import QudiPalettePale as palette

class ManualLACMainWindow(QtWidgets.QMainWindow):
    """ Create the Main Window based on the \*.ui file. """

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'ui_manualLAC.ui')

        # Load it
        super().__init__()
        uic.loadUi(ui_file, self)

class ManualLACGUI(GuiBase):
    """ Main manual LAC control GUI class.
    """
    
    # CONNECTORS #############################################################
    laclogic = Connector(interface='LACLogic')

    # SIGNALS ################################################################
   

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()
        return 0

    def on_activate(self):
        """ Definition and initialisation of the GUI plus staring the measurement.
        """

        # CONNECTORS PART 2 ###################################################
        self._laclogic = self.laclogic()

        self._mw = ManualLACMainWindow()

        # Buttons and spinboxes
        self._mw.startButton.clicked.connect(self.start)
        self._mw.stopButton.clicked.connect(self.stop)
        self._mw.posInput.valueChanged.connect(self.set_pos_input)

        # Connect signals

        self._laclogic.sigUpdateLACDisplay.connect(self.update_display)
        
    def update_display(self):
        """ Updates display with LAC output position.
        """
        self._mw.posOutput.setText(str(round(self._laclogic.position, 3)))

    def set_pos_input(self):
        """ Sets LAC position input using spinbox value.
        """
        self.posInput = self._mw.posInput.value()
        self._laclogic.set_pos(self.posInput)

    def start(self):
        """ Starts LAC logic loop.
        """
        self._laclogic.start()

    def stop(self):
        """ Stops LAC logic loop.
        """
        self._laclogic.stop()
    
    def show(self):
        self._mw.show()