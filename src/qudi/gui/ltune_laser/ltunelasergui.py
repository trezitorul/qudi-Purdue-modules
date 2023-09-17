# -*- coding: utf-8 -*-
# GUI module for Ltune laser


import os
import time

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qtpy import QtWidgets
from qtpy import uic
import numpy as np
from qudi.util.colordefs import QudiPalettePale as palette


class LtuneLaserMainWindow(QtWidgets.QMainWindow):
    """ Create the Main Window based on the *.ui file. """

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'ui_ltune_laser.ui')

        # Load it
        super().__init__()
        uic.loadUi(ui_file, self)


class LtuneLaserGUI(GuiBase):
    """

    """
    
    # CONNECTORS #############################################################
    ltune_laser_logic = Connector(interface='LtuneLaserLogic')

    # SIGNALS ################################################################
    enabled = False

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._ltune_laser_logic.disable_laser()
        self._mw.close()
        #return 0

    def on_activate(self):
        """ 
        Activate the module
        """

        # CONNECTORS PART 2 ###################################################
        self._ltune_laser_logic = self.ltune_laser_logic()

        self._mw = LtuneLaserMainWindow()
        self._pw = self._mw.powerTrace

        # Connect buttons to functions
        self._mw.powerInput.setMaximum(1000)
        self._mw.powerInput.valueChanged.connect(self.set_power)
        self._mw.switchLaser.clicked.connect(self.update_button)
        
        self.power = 0

        # Connect update signal
        # self._ltune_laser_logic.sig_update_laser_display.connect(self.updateDisplay)
        self._ltune_laser_logic.sig_update_laser_display.connect(self.update_plot)

        # set up plot

        self.plot1 = self._pw.plotItem
        self.plot1.setLabel('left', 'Power Output', units='W', color='#00ff00')
        self.plot1.setLabel('bottom')

        self.curve_arr = []
        ## Create an empty plot curve to be filled later, set its pen
        self.curve_arr.append(self.plot1.plot())
        self.curve_arr[-1].setPen(palette.c1)

        self.time_pass = 0
        self.power_output_array = []



    def update_plot(self):
        """ The function that grabs the data and sends it to the plot.
        """
        self.time_pass += 1
        self.power_output_array.append(self._ltune_laser_logic.power)
        # self.power_output_array.append(self._pmlogic.power)
        if (self.time_pass < 200):
            self.curve_arr[0].setData(
                y = np.asarray(self.power_output_array),
                x = np.arange(0, self.time_pass)
                )
        else:
            self.curve_arr[0].setData(
                y = np.asarray(self.power_output_array)[self.time_pass-200, self.time_pass],
                x = np.arange(self.time_pass-200, self.time_pass)
                )


    def set_power(self):
        self.power = self._mw.powerInput.value()

        if (self.enabled):
            self._ltune_laser_logic.set_power(self.power)

    def update_button(self):
        if (self.enabled == False):
            self._ltune_laser_logic.enable_laser()
            self.enabled = True
            if (self.power != 0):
                self._ltune_laser_logic.set_power(self.power)
            self._mw.switchLaser.setText("Disable Laser")
        else:
            self._ltune_laser_logic.disable_laser()
            self.enabled = False
            self._mw.switchLaser.setText("Enable Laser")
    
    def show(self):
        self._mw.show()
