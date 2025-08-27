import os
import numpy as np
import time

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from qtpy import uic

class PolarMotorMainWindow(QtWidgets.QMainWindow):
    """ Create the Main Window based on the \*.ui file. """

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'ui_polarization_motor.ui')

        # Load it
        super().__init__()
        uic.loadUi(ui_file, self)
        # self.show()

class PolarMotordGUI(GuiBase):
    """

    """
    
    # CONNECTORS #############################################################
    polar_logic = Connector(interface='PolarMotorLogic')

    # SIGNALS ################################################################
    sig_start_GUI = QtCore.Signal()


    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)


    def on_activate(self):
        # CONNECTORS PART 2 ###################################################
        self._polar_logic = self.polar_logic()

        self._mw = PolarMotorMainWindow()
        
        # Set default parameters


        # Connect spin boxes
        self._mw.inputDegree.valueChanged.connect(self.update_position)
        self._mw.moveButton.clicked.connect(self.set_pos_input)

        # Connect signals
        self._polar_logic.sig_update_polar_motor_display.connect(self.update_display)


    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()

    def update_position(self):
        self.posInput = self._mw.inputDegree.value()


    def set_pos_input(self):
        self._polar_logic.set_position(self.posInput)


    def update_display(self):
        self._mw.currDegree.setText(str(self._polar_logic.position))

    def show(self):
        self._mw.show()
