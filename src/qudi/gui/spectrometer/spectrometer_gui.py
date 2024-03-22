# -*- coding: utf-8 -*-
"""
Powermeter GUI module that displays power output in mW.

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

class SpectroMeterMainWindow(QtWidgets.QMainWindow):
    """ Create the Main Window based on the *.ui file. """

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'ui_spectrometer_gui.ui')

        # Load it
        super().__init__()
        uic.loadUi(ui_file, self)
        self.show()

class SpectroMeterGUI(GuiBase):
    """ Spectrometer GUI main class.
    """
    
    # CONNECTORS #############################################################
    spmlogic = Connector(interface='SpectrometerLogic')

    # SIGNALS ################################################################
   

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)
        self.is_live = False

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()
        #return 0

    def on_activate(self):
        """ Initialize, connect and configure the powermeter GUI.
        """

        # CONNECTORS PART 2 ###################################################
        self._spmlogic = self.spmlogic()

        self._mw = SpectroMeterMainWindow()
        
        # Plot labels.
        self._pw = self._mw.intensitiesTrace

        self.plot1 = self._pw.plotItem
        self.plot1.setLabel('left', 'Intensity', units='counts', color='#00ff00')
        self.plot1.setLabel('bottom', 'Wave Length', units='nm')

        self.curvearr = []
        ## Create an empty plot curve to be filled later, set its pen
        self.curvearr.append(self.plot1.plot())
        self.curvearr[-1].setPen(palette.c1)

        self.timePass = 0
        self.powerOutputArr = []
        # Set default parameters

        # Connect buttons to functions
        self._mw.startButton.clicked.connect(self.start_collecting)
        self._mw.stopButton.clicked.connect(self.stop_collecting)
        self._mw.liveButton.clicked.connect(self.live_mode_enable)
        self._mw.staticButton.clicked.connect(self._spmlogic.stop)
        self._mw.clearButton.clicked.connect(self._spmlogic.clear)

        self._mw.integrationTime.valueChanged.connect(self.change_integration_time)

        # Connect signals
        self._spmlogic.sig_update_display.connect(self.update_plot)


    def start_collecting(self):
        if self.is_live:
            self._spmlogic.start_live_collection()
        else:
            self._spmlogic.get_intensities()


    def stop_collecting(self):
        if self.is_live:
            self._spmlogic.stop_live_collection()


    def live_mode_enable(self):
        self.is_live = True


    def update_plot(self):
        """ The function that grabs the power output data and sends it to the plot.
        """
        self.timePass += 1
        
        self.curvearr[0].setData(
            y = self._spmlogic.intensities_counts,
            x = self._spmlogic.wavelengths
            )
            
    def show(self):
        self._mw.show()
        self._mw.raise_()
