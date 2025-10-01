import os
import numpy as np
import sys
from qtpy import QtCore
from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qtpy import QtWidgets
from qtpy.QtCharts import QPolarChart, QScatterSeries, QValueAxis
from qtpy import uic
from qudi.util.colordefs import QudiPalettePale as palette
# save dialog class
sys.path.append("C:/Users/Ozymandias/qudi-Purdue-modules/src/qudi/gui")
from save_dialog import SaveDialog

class PolarizationMeasurementMainWindow(QtWidgets.QMainWindow):
    """ Create the Main Window based on the *.ui file. """

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'polarization_measurement.ui')

        # Load it
        super().__init__()
        uic.loadUi(ui_file, self)
        self.show()

class PolarizationMeasurementGUI(GuiBase):
    """
    Polarization Measurement GUI
    """

    #Connector
    polarization_measurement_logic = Connector(interface='polarization_measurement_logic')
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
        """ Activate the module
        """
        self._polarization_measurement_logic = self.polarization_measurement_logic()
        self._mw = PolarizationMeasurementMainWindow()
        self._save_dialog = SaveDialog(self._mw)

        self._polarization_measurement_logic.sig_update_display.connect(self.update_plot)

        #self._mw.galvoUpButton.clicked.connect(lambda: self.move_galvo(1,1))

        # Plot labels for 1st channel.
        self.chart_view = self._mw.polar_plot

        self.polar_chart = QPolarChart()

        # change title here based on flag? but might need logic
        self.polar_chart.setTitle(self._polarization_measurement_logic.get_plot_title())
        
        self.polar_data = QScatterSeries()
        self.polar_data.setName("Polarization Data")
        self.polar_data.setMarkerSize(10)
        
        self.polar_chart.addSeries(self.polar_data)

        # Configure angular axis
        angular_axis = QValueAxis()
        angular_axis.setRange(0, 360)
        angular_axis.setLabelFormat("%.0f")
        angular_axis.setTitleText("Angle (degrees)")
        self.polar_chart.addAxis(angular_axis, QPolarChart.PolarOrientationAngular)
        self.polar_data.attachAxis(angular_axis)

        # Configure radial axis
        radial_axis = QValueAxis()
        radial_axis.setRange(0, 36)
        radial_axis.setLabelFormat("%.1f")
        radial_axis.setTitleText("Radius")
        self.polar_chart.addAxis(radial_axis, QPolarChart.PolarOrientationRadial)
        self.polar_data.attachAxis(radial_axis)

        # Add chart to the view
        self.chart_view.setChart(self.polar_chart)

        #Setup Buttons
        self._mw.save_scan_button.clicked.connect(self.save_scan_data)
        self._mw.start_scan_button.clicked.connect(self.start_measurement)
        self._mw.stop_scan_button.clicked.connect(self.stop_measurement)

        #Connect Signals
        self.sigSaveScan.connect(self.polarization_measurement_logic().initiate_save, QtCore.Qt.QueuedConnection)
        self.sigSaveFinished.connect(self._save_dialog.hide, QtCore.Qt.QueuedConnection)
        self.polarization_measurement_logic().sigSaveStateChanged.connect(self._track_save_status)
        # self.sigShowSaveDialog.connect(lambda x: self._save_dialog.show() if x else self._save_dialog.hide(), QtCore.Qt.DirectConnection)
        self._polarization_measurement_logic.sigRequestSaveDialog.connect(self._on_save_dialog_requested) # for save dialog

        #Set Defaults
        self._mw.stop_angle.setValue(360)
        self._mw.step_size.setValue(15)
        self._mw.int_time.setValue(100)

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()
        #return 0

    def count(self):
        pass

    def start_measurement(self):
        self.polar_data.clear()
        start_angle=self._mw.start_angle.value()
        stop_angle=self._mw.stop_angle.value()
        step_size=self._mw.step_size.value()
        int_time=self._mw.int_time.value()
        angles=[angle/10.0 for angle in range(int(10*start_angle), int(10*stop_angle), int(10*step_size))]
        self._polarization_measurement_logic.set_scan_parameters(int_time, angles)
        self._polarization_measurement_logic.initiate_measurement()

    def stop_measurement(self):
        self._polarization_measurement_logic.halt_measurement()

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
            self._polarization_measurement_logic.sigSaveDialogExec.emit(filename, notes)
        else:
            filename, notes = dialog.get_data()
            self._last_filename = filename
            self._last_notes = notes
            self._polarization_measurement_logic.sigSaveDialogExec.emit(filename, notes)

    def update_plot(self):
        print("PLOTTING DATA")
        self.polar_data.append(self._polarization_measurement_logic.data[-1][0], self._polarization_measurement_logic.data[-1][1])
        max_radius = max(point.y() for point in self.polar_data.points())
        self.polar_chart.axes()[1].setRange(0, max_radius + 1)

    def _track_save_status(self, in_progress):
        if in_progress:
            self._n_save_tasks += 1
        else:
            self._n_save_tasks -= 1

        if self._n_save_tasks == 0:
            self.sigSaveFinished.emit()

    def show(self):
        self._mw.show()

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


