# -*- coding: utf-8 -*-
# GUI module for piezo

import os

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from qtpy import uic
from qudi.util.colordefs import QudiPalettePale as palette

class PiezoMainWindow(QtWidgets.QMainWindow):
    """ Create the Main Window based on the *.ui file. """

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'ui_APTpiezo_gui.ui')

        # Load it
        super().__init__()
        uic.loadUi(ui_file, self)
        self.show()

class PiezoGUI(GuiBase):
    """
    Main GUI functionalities
    """
    
    # CONNECTORS #############################################################
    apt_logic = Connector(interface='LogicBase')

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()
        #return 0

    def on_activate(self):
        """ 
        On activate of the GUI
        
        No return
        """

        # CONNECTORS PART 2 ###################################################
        self._apt_logic = self.apt_logic()

        self._mw = PiezoMainWindow()

        # Set default parameters
        self.position = [0, 0, 0]
        self._mw.StepSize.setValue(10)
        self.step_size = 10
        self.is_manual = True

        # Connect buttons to functions
        self._mw.StepSize.valueChanged.connect(self.step_changed)
        # self._mw.inputX.valueChanged.connect(self.manual_input)
        # self._mw.inputY.valueChanged.connect(self.manual_input)
        # self._mw.inputZ.valueChanged.connect(self.manual_input)

        self._mw.upButton.clicked.connect(lambda: self.move(1,1))
        self._mw.downButton.clicked.connect(lambda: self.move(1,-1))
        self._mw.leftButton.clicked.connect(lambda: self.move(0,-1))
        self._mw.rightButton.clicked.connect(lambda: self.move(0,1))
        self._mw.zUpButton.clicked.connect(lambda: self.move(2,1))
        self._mw.zDownButton.clicked.connect(lambda: self.move(2,-1))
        self._mw.switchMode.clicked.connect(self.update_button)

        self._mw.moveManual.clicked.connect(self.manual_input)

        # Connect update signal
        self._apt_logic.sig_update_display.connect(self.update_display)
        self.show()


    def move(self, axis, direction):
        """Move piezo

        Args:
            axis (int): 0->x, 1->y, 2->z
            direction (int, optional): Step direction. Defaults to 1.
        """
        if (not self.is_manual):
            position = self.position
            position[axis] = self.position[axis] + self.step_size * direction

            self._apt_logic.set_position(position)


    def step_changed(self):
        """ When the step_size is changed
        """
        self.step_size = self._mw.StepSize.value()

    def manual_input(self):
        """ Check if the user wants to manually input the position
        """
        if (self.is_manual):
            position = [self._mw.inputX.value(), self._mw.inputY.value(), self._mw.inputZ.value()]
            self.position = position
            self._apt_logic.set_position(position)


    def update_display(self):
        """ Update the GUI display
        """
        self.position = self._apt_logic.position
        self._mw.xVal.setText(str(self.position[0]))
        self._mw.yVal.setText(str(self.position[1]))
        self._mw.zVal.setText(str(self.position[2]))
        if (not self.is_manual):
            self._mw.inputX.setValue(self.position[0])
            self._mw.inputY.setValue(self.position[1])
            self._mw.inputZ.setValue(self.position[2])

    def show(self):
        """Make main window visible and put it above all other windows. """
        # Show the Main GUI:
        self._mw.show()
        self._mw.activateWindow()
        self._mw.raise_()


    def update_button(self):
        """ Update the button text
        """
        if (self.is_manual == False):
            self.is_manual = True
            self._mw.switchMode.setText("Move by Input")
        else:
            self.is_manual = False
            self._mw.switchMode.setText("Move by Step")
