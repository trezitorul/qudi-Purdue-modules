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
import time
from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from qtpy import uic
from qudi.util.colordefs import QudiPalettePale as palette
class SaveDialog(QtWidgets.QDialog):
    """ Dialog to provide feedback and block GUI while saving """
    def __init__(self, parent, title="Please wait", text="Saving..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)

        # Dialog layout
        self.text = QtWidgets.QLabel("<font size='16'>" + text + "</font>")
        self.hbox = QtWidgets.QHBoxLayout()
        self.hbox.addSpacerItem(QtWidgets.QSpacerItem(50, 0))
        self.hbox.addWidget(self.text)
        self.hbox.addSpacerItem(QtWidgets.QSpacerItem(50, 0))
        self.setLayout(self.hbox)
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
    """ G2 Measurement Main Window
    """
    time0=0
    ns=1E-9
    # CONNECTORS #############################################################
    qtlogic = Connector(interface='QuTagLogic')
    g2channels = [1,2]#hardcoded for now
    histWidth=30
    bin_count=1024
    # SIGNALS ################################################################
    sigSaveScan = QtCore.Signal()
    sigSaveFinished = QtCore.Signal()
    sigShowSaveDialog = QtCore.Signal(bool)

    def __init__(self, config, **kwargs):

        super().__init__(config=config, **kwargs)
        self._n_save_tasks = 0

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
        self._save_dialog = SaveDialog(self._mw)
        # Plot labels.
        self._pw = self._mw.qutag_histogram

        self.plot1 = self._pw.plotItem
        self.plot1.setLabel('left', 'Normalized Counts')
        self.plot1.setLabel('bottom', 'Time (ns)')
        self.plot1.setYRange(0,1.2)

        self.curvearr = []
        ## Create an empty plot curve to be filled later, set its pen
        self.curvearr.append(self.plot1.plot())
        self.curvearr[-1].setPen(palette.c1)

        self.timePass = 0
        self.powerOutputArr = []
        # Set default parameters

        # Connect buttons to functions
        self._mw.start_button.clicked.connect(self.start_collecting)
        self._mw.stop_button.clicked.connect(self.stop_collecting)
        self._mw.reset_button.clicked.connect(self.reset)

        self._mw.hist_width_spinbox.setValue(self.histWidth)
        self._mw.bin_count_spinbox.setValue(self.bin_count)
        self._mw.save_button.clicked.connect(self.save_scan_data)

        # Connect spinboxes
        # self._mw.hist_width_spinbox.valueChanged.connect()
        # self._mw.bin_count_spinbox.valueChanged.connect()

        # Connect signals
        self._qtlogic.sig_update_display.connect(self.update_text_display)
        self._qtlogic.sig_update_display.connect(self.update_plot)
        self.sigSaveScan.connect(self.qtlogic().initiate_save, QtCore.Qt.QueuedConnection)
        self.sigSaveFinished.connect(self._save_dialog.hide, QtCore.Qt.QueuedConnection)
        self.qtlogic().sigSaveStateChanged.connect(self._track_save_status)
        self.sigShowSaveDialog.connect(lambda x: self._save_dialog.show() if x else self._save_dialog.hide(),
                                       QtCore.Qt.DirectConnection)


    def update_text_display(self):
        """ Updates display text with current rates, events, and the total time integrated
        """
        liveInfo=self._qtlogic.getHBTLiveInfo()
        rates=self._qtlogic.get_count_rates([1,2])
        self._mw.rates_ch1.setText(str(rates[0]))
        self._mw.rates_ch2.setText(str(rates[1]))
        self._mw.events_ch1.setText(str(liveInfo[0]))
        self._mw.time_output.setText(str(self._qtlogic.getHBTIntegrationTime()))

    def __get_save_scan_data_func(self):
        def save_scan_func():
            self.save_scan_data()
        return save_scan_func

    def update_plot(self):
        """ The function that grabs the power output data and sends it to the plot.
        """
        # g2_calc
        self.curvearr[0].setData(
            y = self._qtlogic.counts,
            x = self._qtlogic.time
            )

    def start_collecting(self):
        self._qtlogic.updateG2Config(self._mw.hist_width_spinbox.value(), self._mw.bin_count_spinbox.value())
        self._qtlogic.start()
        self.time0=time.perf_counter()

    def stop_collecting(self):
        self._qtlogic.stop()

    def reset(self):
        self._qtlogic.reset()

    def get_integration_time(self):
        return time.perf_counter() - self.time0


    # def getdata(self):
    #     self._qtlogic.usedata(self._mw.hist_width_spinbox.value)
    @QtCore.Slot(tuple)
    def save_scan_data(self, scan_axes=None):
        """
        Save data for a given (or all) scan axis.
        @param tuple: Axis to save. Save all currently displayed if None.
        """
        self.sigShowSaveDialog.emit(True)
        try:
            self.sigSaveScan.emit()
        finally:
            pass

    def _track_save_status(self, in_progress):
        if in_progress:
            self._n_save_tasks += 1
        else:
            self._n_save_tasks -= 1

        if self._n_save_tasks == 0:
            self.sigSaveFinished.emit()

    def show(self):
        self._mw.show()
        self._mw.raise_()
