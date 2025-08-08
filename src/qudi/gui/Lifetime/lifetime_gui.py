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
import sys
import numpy as np
import time
from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from qtpy import uic
from qudi.util.colordefs import QudiPalettePale as palette
# save dialog class
from qudi.gui.save_dialog import SaveDialog

class LifetimeMainWindow(QtWidgets.QMainWindow):
    """ Create the Main Window based on the *.ui file. """
    
    def __init__(self):
        
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'ui_lifetime.ui')

        # Load it
        super().__init__()
        uic.loadUi(ui_file, self)
        self.show()

class LifetimeGUI(GuiBase):
    """ Lifetime Measurement Main Window
    """
    time0=0
    ns=1E-9
    ps = ns*1E-3
    # CONNECTORS #############################################################
    qtlogic = Connector(interface='QuTagLogic')
    histWidth=1 #nanoseconds
    bin_count=256 #Number of bins in the histogram
    # SIGNALS ################################################################
    sigSaveScan = QtCore.Signal()
    sigSaveFinished = QtCore.Signal()
    sigShowSaveDialog = QtCore.Signal(bool)

    def __init__(self, config, **kwargs):
        """ Initialize the Lifetime GUI."""
        super().__init__(config=config, **kwargs)
        self._n_save_tasks = 0

        # for persisting?
        self._last_filename = ""
        self._last_notes = ""

    def on_deactivate(self):
        """ Reverse steps of activation

        Returns:
            n int: error code (0:OK, -1:error)
        """
        self._mw.close()
        #return 0

    def on_activate(self):
        """ Initialize, connect and configures the Lifetime GUI. This is where the plotter is configured along with all of the signals required.
        """

        # CONNECTORS PART 2 ###################################################
        self._qtlogic = self.qtlogic()

        self._mw = LifetimeMainWindow()
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
        self.sigSaveScan.connect(self._qtlogic.initiate_lifetime_save, QtCore.Qt.QueuedConnection)
        self.sigSaveFinished.connect(self._save_dialog.hide, QtCore.Qt.QueuedConnection)
        self._qtlogic.sigSaveStateChanged.connect(self._track_save_status)
        # self.sigShowSaveDialog.connect(lambda x: self._save_dialog.show() if x else self._save_dialog.hide(),
        #                                QtCore.Qt.DirectConnection)
        self._qtlogic.sigRequestSaveDialog.connect(self._on_save_dialog_requested) # for save dialog


    def update_text_display(self):
        """ Updates the display with the current stats for the lifetime measurement. 
        This includes the number of start and stop events, along with the total integration time elapsed. 
        This function is triggered by the logic module.
        """
        
        if self._qtlogic.measurement_type == "LIFETIME":
            liveInfo=self._qtlogic.getLFTLiveInfo()
            self._mw.start_events.setText(str(liveInfo[1]))
            self._mw.stop_events.setText(str(liveInfo[2]))
            self._mw.int_time.setText(str(round(liveInfo[3]*self.ps,1)))

    def __get_save_scan_data_func(self):
        def save_scan_func():
            self.save_scan_data()
        return save_scan_func

    def update_plot(self):
        """ This function is triggered by the logic module to update the plot with the current lifetime histogram data.
        """
        # check if the measurement type is LIFETIME type of measurement and update the plot.
        if self._qtlogic.measurement_type == "LIFETIME":
            self.curvearr[0].setData(
            y = self._qtlogic.counts,
            x = self._qtlogic.time
            )

    def start_collecting(self):
        """ Start the lifetime measurement by setting the measurement type and updating the configuration with the values set in the GUI. 
        This is triggered by the start button in the GUI."""
        self._qtlogic.measurement_type = "LIFETIME"
        self._qtlogic.updateConfig(self._mw.hist_width_spinbox.value(), self._mw.bin_count_spinbox.value())
        self._qtlogic.start("LIFETIME")
        self.time0=time.perf_counter()

    def stop_collecting(self):
        """ Calls the logic module to stop the lifetime measurement. Triggered by the stop button in the GUI."""
        self._qtlogic.stop()

    def reset(self):
        """ Calls the reset function in the logic module to reset the lifetime measurement. This clears all of the data and clears the buffers of the time tagger."""
        self._qtlogic.reset()

    def get_integration_time(self):
        return time.perf_counter() - self.time0


    # def getdata(self):
    #     self._qtlogic.usedata(self._mw.hist_width_spinbox.value)
    @QtCore.Slot(tuple)
    def save_scan_data(self, scan_axes=None):
        """
        Save data for a given (or all) scan axis.
        Args:
            scan_axes (int): Axis to save. Save all currently displayed if None. 
        """
        self.sigShowSaveDialog.emit(True)
        try:
            self.sigSaveScan.emit()
        finally:
            pass
    
    # sending file name and notes
    @QtCore.Slot()
    def _on_save_dialog_requested(self):
        dialog = SaveDialog(self._mw, default_filename=self._last_filename, default_notes=self._last_notes)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            filename, notes = dialog.get_data()
            self._last_filename = filename
            self._last_notes = notes
            self._qtlogic.sigSaveDialogExec.emit(filename, notes)
        else:
            self._qtlogic.sigSaveDialogExec.emit("", "")

    def _track_save_status(self, in_progress):
        """ Track the number of save tasks in progress and emit a signal when all are finished. 
        This is used to manage the save dialog visibility and to avoid multithreading issues."""

        if in_progress:
            self._n_save_tasks += 1
        else:
            self._n_save_tasks -= 1

        if self._n_save_tasks == 0:
            self.sigSaveFinished.emit()

    def show(self):
        """ Show the main window and raise it to the front. """
        self._mw.show()
        self._mw.raise_()


# class SaveDialog(QtWidgets.QDialog):
#     """ Dialog to provide feedback and block GUI while saving """
#     def __init__(self, parent, default_filename="", default_notes=""):
#         super().__init__(parent)
        
#         self.setWindowTitle("Saving...")
#         self.setWindowModality(QtCore.Qt.WindowModal)
#         self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)
        
#         # text box for experiment name
#         self.name_label = QtWidgets.QLabel("Experiment/Sample Name:")
#         self.name_edit = QtWidgets.QLineEdit()
#         self.name_edit.setPlaceholderText("e.g. test_run_01")

#         # text box for notes
#         self.notes_label = QtWidgets.QLabel("Notes (optional):")
#         self.notes_edit = QtWidgets.QPlainTextEdit()
#         self.notes_edit.setPlaceholderText("Add notes or observations...")
        
#         # persistennce
#         self.name_edit.setText(default_filename)
#         self.notes_edit.setPlainText(default_notes)

#         self.save_button = QtWidgets.QPushButton("Save")
#         self.save_button.setEnabled(False)  # disabled until name is entered

#         layout = QtWidgets.QVBoxLayout()
#         layout.addWidget(self.name_label)
#         layout.addWidget(self.name_edit)
#         layout.addWidget(self.notes_label)
#         layout.addWidget(self.notes_edit)
#         layout.addWidget(self.save_button)
#         self.setLayout(layout)

#         # --- Connections
#         self.name_edit.textChanged.connect(self._on_name_changed)
#         self.save_button.clicked.connect(self.accept)

#     def _on_name_changed(self, text):
#         self.save_button.setEnabled(bool(text.strip()))

#     def get_data(self):
#         return self.name_edit.text().strip(), self.notes_edit.toPlainText().strip()

#     # just for QOL because it closes out normally if you x out
#     # i think reject (for pyside5) is a protected function so should be ok to call???
#     def reject(self):
#         if not self.name_edit.text().strip():
#             msg = QtWidgets.QMessageBox(self)
#             msg.setIcon(QtWidgets.QMessageBox.Warning)
#             msg.setWindowTitle("Quit without saving?")
#             msg.setText("You haven't entered a file name for this experiment.\nDo you want to go back and enter one?")
#             msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
#             msg.setDefaultButton(QtWidgets.QMessageBox.Yes)
#             response = msg.exec_()

#             if response == QtWidgets.QMessageBox.Yes:
#                 return  # don't close the dialog
#         super().reject()  # proceed with closing


        # self.scan_name = QtWidgets.QLabel("Experiment/Sample Name:")
        # self.name_edit = QtWidgets.QLineEdit()
        # self.name_edit.setPlaceholderText("e.g. test_run_01")

        # self.setWindowModality(QtCore.Qt.WindowModal)
        # self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)

        # # Dialog layout
        # self.text = QtWidgets.QLabel("<font size='16'>" + text + "</font>")
        # self.hbox = QtWidgets.QHBoxLayout()
        # self.hbox.addSpacerItem(QtWidgets.QSpacerItem(50, 0))
        # self.hbox.addWidget(self.text)
        # self.hbox.addSpacerItem(QtWidgets.QSpacerItem(50, 0))
        # self.setLayout(self.hbox)