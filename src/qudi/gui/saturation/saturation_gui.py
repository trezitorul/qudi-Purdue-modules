import os
import sys
from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qtpy import QtWidgets
from qtpy import uic
from qtpy import QtCore
from qudi.util.colordefs import QudiPalettePale as palette
# save dialog class
from qudi.gui.save_dialog import SaveDialog

class CounterMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, "saturation_measurement.ui")

        super().__init__()
        uic.loadUi(ui_file, self)
        self.show()

class Saturation_GUI(GuiBase):
    """
    Saturation Measurement Module
    """
    saturation_measurement_logic = Connector(interface="SaturationLogic")

    #Signals
    sigSaveScan = QtCore.Signal()
    sigSaveFinished = QtCore.Signal()
    sigShowSaveDialog = QtCore.Signal(bool)

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)
        self._n_save_tasks = 0

        # for persisting?
        self._last_filename = ""
        self._last_notes = ""

    def on_activate(self):
        self._mw = CounterMainWindow()
        self._save_dialog = SaveDialog(self._mw)
        #Hook Up Connectors
        self._sat_logic = self.saturation_measurement_logic()
        #Connect Signals
        self._sat_logic.sigUpdateDisplay.connect(self.update_plot)

        #Configure Live Plot
        self.plot_window = self._mw.saturation_plot
        self.plot = self.plot_window.plotItem
        self.plot.setLabel("left", "Count Rate", units = "cps")
        self.plot.setLabel("bottom", "Power ", units = "uW")
        self.curves=[]
        print(self._sat_logic.counter_channels)
        for key in self._sat_logic.counter_channels:
            curve = self.plot.plot(name=key)
            curve.setPen(palette.c1)
           # curve.setOpts(name=key)
            self.curves.append(curve)

        #Connect Buttons
        self._mw.start_measurement_bt.clicked.connect(self.start_measurement)
        self._mw.stop_measurement_bt.clicked.connect(self.stop_measurement)
        self._mw.save_measurement_bt.clicked.connect(self.save_scan_data)

        #Connect Spin Boxes
        self.start_power=50
        self._mw.start_power_sb.setValue(self.start_power)
        self._mw.start_power_sb.valueChanged.connect(self.update_start_power)

        self.stop_power=2000
        self._mw.stop_power_sb.setValue(self.stop_power)
        self._mw.stop_power_sb.valueChanged.connect(self.update_stop_power)

        self.steps=100
        self._mw.steps_sb.setValue(self.steps)
        self._mw.steps_sb.valueChanged.connect(self.update_steps)

        self.num_ints = 1
        self._mw.num_ints_sb.setValue(self.num_ints)
        self._mw.num_ints_sb.valueChanged.connect(self.update_num_ints)

        self.int_time=100
        self._mw.int_time_sb.setValue(self.int_time)
        self._mw.int_time_sb.valueChanged.connect(self.update_int_time)

        self.sigSaveScan.connect(self._sat_logic.initiate_save, QtCore.Qt.QueuedConnection)
        self.sigSaveFinished.connect(self._save_dialog.hide, QtCore.Qt.QueuedConnection)
        self._sat_logic.sigSaveStateChanged.connect(self._track_save_status)
        # self.sigShowSaveDialog.connect(lambda x: self._save_dialog.show() if x else self._save_dialog.hide(), QtCore.Qt.DirectConnection)
        self._sat_logic.sigRequestSaveDialog.connect(self._on_save_dialog_requested) # for save dialog


    def on_deactivate(self):
        self._mw.close()


    def update_plot(self):
        self.power_data = [self._sat_logic.data[i][1] for i in range(len(self._sat_logic.data))]
        curve_num = 0
        for curve in self.curves:
            self.count_data = [self._sat_logic.data[i][3+2*curve_num] for i in range(len(self._sat_logic.data))]
            curve_num=curve_num+1
            curve.setData(self.power_data, self.count_data)
    
    def start_measurement(self):
        self._sat_logic.configure_scan(self.start_power, self.stop_power, self.steps, self.int_time, self.num_ints)
        self._sat_logic.initiate_measurement()

    def stop_measurement(self):
        self._sat_logic.halt_measurement()

    def update_start_power(self, start_power):
        self.start_power = start_power

    def update_stop_power(self, stop_power):
        self.stop_power = stop_power

    def update_steps(self, steps):
        self.steps = steps

    def update_num_ints(self, num_ints):
        self.num_ints = num_ints

    def update_int_time(self, int_time):
        self.int_time = int_time

    def show(self):
        self._mw.show()
        self._mw.raise_()

    @QtCore.Slot(tuple)
    def save_scan_data(self):
        """
        Save data for a given (or all) scan axis.
        @param tuple: Axis to save. Save all currently displayed if None.
        """
        self.sigShowSaveDialog.emit(True)
        try:
            self.sigSaveScan.emit()
        finally:
            pass

    # sending file name and notes
    @QtCore.Slot()
    def _on_save_dialog_requested(self):
        dialog = SaveDialog(
            self._mw,
            default_filename=self._last_filename,
            default_notes=self._last_notes
        )

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            filename, notes = dialog.get_data()
            self._last_filename = filename
            self._last_notes = notes
            self._sat_logic.sigSaveDialogExec.emit(filename, notes)
        else:
            filename, notes = dialog.get_data()
            self._last_filename = filename
            self._last_notes = notes
            self._sat_logic.sigSaveDialogExec.emit(filename, notes)

        # if x out, save whatever is in the text boxes bc at the moment its just saving as the default filename

    def _track_save_status(self, in_progress):
        if in_progress:
            self._n_save_tasks += 1
        else:
            self._n_save_tasks -= 1

        if self._n_save_tasks == 0:
            self.sigSaveFinished.emit()

# class SaveDialog(QtWidgets.QDialog):
#     """ Dialog to provide feedback and block GUI while saving """
#     def __init__(self, parent, title="Please wait", text="Saving..."):
#         super().__init__(parent)
#         self.setWindowTitle(title)
#         self.setWindowModality(QtCore.Qt.WindowModal)
#         self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)

#         # Dialog layout
#         self.text = QtWidgets.QLabel("<font size='16'>" + text + "</font>")
#         self.hbox = QtWidgets.QHBoxLayout()
#         self.hbox.addSpacerItem(QtWidgets.QSpacerItem(50, 0))
#         self.hbox.addWidget(self.text)
#         self.hbox.addSpacerItem(QtWidgets.QSpacerItem(50, 0))
#         self.setLayout(self.hbox)
