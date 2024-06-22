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

class QuTagMainWindow(QtWidgets.QMainWindow):
    """ Create the Main Window based on the *.ui file. """

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'ui_qutag.ui')

        # Load it
        super().__init__()
        uic.loadUi(ui_file, self)
        self.show()

class QuTagGUI(GuiBase):
    """ Power meter GUI main class.
    """
    
    # CONNECTORS #############################################################
    qtlogic = Connector(interface='QuTagLogic')

    # SIGNALS ################################################################
   

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

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
        self._qtlogic = self.qtlogic()

        self._mw = QuTagMainWindow()
        
        # Plot labels.
        self._pw = self._mw.qutag_histogram

        self.plot1 = self._pw.plotItem
        self.plot1.setLabel('left', 'Normalized Counts')
        self.plot1.setLabel('bottom', 'Time')

        self.curvearr = []
        ## Create an empty plot curve to be filled later, set its pen
        self.curvearr.append(self.plot1.plot())
        self.curvearr[-1].setPen(palette.c1)

        self.timePass = 0
        self.powerOutputArr = []
        # Set default parameters

        # Connect buttons to functions
        self._mw.start_button.clicked.connect(self._qtlogic.start)
        self._mw.stop_button.clicked.connect(self._qtlogic.stop)
        # self._mw.reset_button.clicked.connect()
        # self._mw.save_button.clicked.connect()

        # Connect spinboxes
        # self._mw.hist_width_spinbox.valueChanged.connect()
        # self._mw.bin_count_spinbox.valueChanged.connect()

        # Connect signals
        # self._qtlogic.sig_update_display.connect(self.update_text_display)
        self._qtlogic.sig_update_display.connect(self.update_plot)


    def update_text_display(self):
        """ Updates display text with current output power in mW.
        """
        self._mw.rates_output.setText(str(self._qtlogic.rates))
        self._mw.events_output.setText(str(self._qtlogic.events))
        self._mw.time_output.setText(str(self._qtlogic.time))


    def update_plot(self):
        """ The function that grabs the power output data and sends it to the plot.
        """
        # g2_calc
        print(self._qtlogic.counts)
        self.curvearr[0].setData(
            y = self._qtlogic.counts,
            x = self._qtlogic.time
            )

    def start_collecting(self):
        self._qtlogic.start_live_collection()


    def stop_collecting(self):
        self._qtlogic.stop_live_collection()


    # def getdata(self):
    #     self._qtlogic.usedata(self._mw.hist_width_spinbox.value)


    def show(self):
        self._mw.show()
        self._mw.raise_()
