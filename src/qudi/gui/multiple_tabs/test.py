import sys
import os
from PyQt5 import QtWidgets, uic
import numpy as np

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qudi.util.colordefs import QudiPalettePale as palette

from qudi.gui.ltune_laser import LtuneLaserGUI
from qudi.gui.Piezo import PiezoGUI
from qudi.gui.flippermirror import FlipperGUI


class DashboardMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'multiple_tabs.ui').replace("\\","/")

        parent_dir = os.path.dirname(os.path.dirname(this_dir))
        flippermirror_ui_path = os.path.join(parent_dir, 'gui', 'flippermirror', 'ui_flippermirror_gui.ui').replace("\\","/")

        # Load it
        super().__init__()
        uic.loadUi(ui_file, self)
        
        # Load the QMainWindow UI into a separate QMainWindow object
        self.flipper_tab_main_window = QtWidgets.QMainWindow(self.flipper_tab)
        self.flipper_tab_ui = uic.loadUi(flippermirror_ui_path, self.flipper_tab_main_window)
        
        # Get the central widget from the QMainWindow
        central_widget = self.flipper_tab_main_window.centralWidget()

        # Create a layout for the tab and add the central widget to it
        self.flipper_layout = QtWidgets.QVBoxLayout(self.flipper_tab)
        self.flipper_layout.addWidget(central_widget)
        
        self.show()

class DashboardGUI(GuiBase):
    laser_tab = LtuneLaserGUI()
    piezo_tab = PiezoGUI()
    flipper_tab = FlipperGUI()
    
    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self.laser_tab.on_deactivate()
        self.piezo_tab.on_deactivate()
        self.flipper_tab.on_deactivate()
        
        self._mw.close()
        #return 0

    def on_activate(self):
        self._mw = DashboardMainWindow()

        self.laser_tab.on_activate()
        self.piezo_tab.on_activate()
        self.flipper_tab.on_activate()
        
        pass


# if __name__ == '__main__':
#     app = QtWidgets.QApplication(sys.argv)
#     window = DashboardMainWindow()
#     sys.exit(app.exec_())
