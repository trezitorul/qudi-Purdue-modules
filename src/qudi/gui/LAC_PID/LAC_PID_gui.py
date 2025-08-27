# -*- coding: utf-8 -*-

"""
This file contains a gui for PID LAC control using the powermeter.

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
import time

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from PySide2 import QtCore, QtWidgets
from qudi.util.uic import loadUi

class LACPIDMainWindow(QtWidgets.QMainWindow):
    """ Create the Main Window based on the \*.ui file. """

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'ui_LAC_PID_gui.ui')

        # Load it
        super().__init__()
        loadUi(ui_file, self)

class LACPIDGUI(GuiBase):
    """ Main GUI class for LAC PID control.
    """
    
    # CONNECTORS #############################################################
    pmlogic = Connector(interface='PowerMeterLogic')
    pidlogic = Connector(interface='ModPIDController')
    laclogic = Connector(interface='LACLogic')

    # SIGNALS ################################################################
    sigStartGUI = QtCore.Signal()


    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)


    def on_activate(self):
        """ Definition and initialisation of the GUI plus staring the measurement.
        """
        # CONNECTORS PART 2 ###################################################
        self._pmlogic = self.pmlogic()
        self._pidlogic = self.pidlogic()
        self._laclogic = self.laclogic()

        self._mw = LACPIDMainWindow()
        
        # Set default parameters
        self._mw.k_P.setValue(self._pidlogic.kP)
        self._mw.k_I.setValue(self._pidlogic.kI)
        self._mw.k_D.setValue(self._pidlogic.kD)

        # Connect buttons to functions
        self._mw.startButton.clicked.connect(self.start)
        self._mw.stopButton.clicked.connect(self.stop)

        # Connect spin boxes
        self._mw.powerInput.valueChanged.connect(self.set_power_input)

        self._mw.k_P.valueChanged.connect(self.change_kP)
        self._mw.k_I.valueChanged.connect(self.change_kI)
        self._mw.k_D.valueChanged.connect(self.change_kD)

        # Connect signals
        self._pidlogic.sigUpdatePIDDisplay.connect(self.update_display)

        self._laclogic.sigUpdateLACDisplay.connect(self.update_display)



    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()
        return 0


    def update_display(self):
        """ Updates display with output position
        """
        self._mw.posOutput.setText(str(round(self._pidlogic.cv, 3)))


    def set_power_input(self):
        """ Sets desired power input (the PID setpoint) using the spinbox.
        """
        self.powerInput = self._mw.powerInput.value()
        self._pidlogic.set_setpoint(self.powerInput)


    def start(self):
        """ Uses signal to start PID loop and uses function to start powermeter loop.
        """
        self._pidlogic.sigStartPID.emit()

        self._pmlogic.start()


    def stop(self):
        """ Stops PID loop and powermeter loop.
        """
        self._pidlogic.sigStopPID.emit()
        self._pmlogic.stop()


    def change_kP(self):
        """ Changes kP value using spinbox.
        """
        kp = self._mw.k_P.value()
        self._pidlogic.set_kp(kp)


    def change_kI(self):
        """ Changes kI value using spinbox.
        """
        ki = self._mw.k_I.value()
        self._pidlogic.set_ki(ki)


    def change_kD(self):
        """ Changes kD value using spinbox.
        """
        kd = self._mw.k_D.value()
        self._pidlogic.set_kd(kd)

    def show(self):
        self._mw.show()
