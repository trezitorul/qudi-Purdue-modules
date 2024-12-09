import os
import numpy as np

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qtpy import QtWidgets
from qtpy.QtCharts import QPolarChart, QScatterSeries, QValueAxis
from qtpy import uic
from qudi.util.colordefs import QudiPalettePale as palette

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

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def on_activate(self):
        """ Activate the module
        """
        self._polarization_measurement_logic = self.polarization_measurement_logic()
        self._mw = PolarizationMeasurementMainWindow()

        self._polarization_measurement_logic.sig_update_display.connect(self.update_plot)

        #self._mw.galvoUpButton.clicked.connect(lambda: self.move_galvo(1,1))

        # Plot labels for 1st channel.
        self.chart_view = self._mw.polar_plot

        self.polar_chart = QPolarChart()

        self.polar_chart.setTitle("Polarization Measurement")
        

        self.polar_data = QScatterSeries()
        self.polar_data.setName("Polarization Data")
        self.polar_data.setMarkerSize(10)
        #TEST DATA
        #for angle in range(0, 360, 10):
        #    r = angle / 10.0
        #    self.polar_data.append(angle, r)
        
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
        self._polarization_measurement_logic.scan_angles=[i for i in range(0,360,10)]
        self._polarization_measurement_logic.start_measurement_loop()

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()
        #return 0

    def count(self):
        pass


    def update_plot(self):
        print("PLOTTING DATA")
        self.polar_data.append(self._polarization_measurement_logic.data[-1][0], self._polarization_measurement_logic.data[-1][1])
        max_radius = max(point.y() for point in self.polar_data.points())
        self.polar_chart.axes()[1].setRange(0, max_radius + 1)

    def show(self):
        self._mw.show()


