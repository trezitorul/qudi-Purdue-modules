# -*- coding: utf-8 -*-
# GUI module for the Galvo

import os
from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from PySide2 import QtWidgets
from qudi.util.uic import loadUi

class GalvoMainWindow(QtWidgets.QMainWindow):
    """ Create the Main Window based on the *.ui file. """

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'ui_galvogui.ui')

        # Load it
        super().__init__()
        loadUi(ui_file, self)


class GalvoGUI(GuiBase):
    """
    Galvo gui.
    """

    #Connector
    galvo_logic = Connector(interface='GalvoLogic')

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def on_activate(self):
        self._galvo_logic = self.galvo_logic()

        self._mw = GalvoMainWindow()

        # Set default parameters
        self._mw.GalvoStepSize.setValue(10)
        self.galvo_position = [0, 0]
        self._mw.posButton.setChecked(True)
        self.galvo_step_size = 10
        self.is_pos_mode = True

        # Units
        self.m=1
        self.um=self.m*1e-6

        # Connect buttons to functions
        self._mw.galvoUpButton.clicked.connect(lambda: self.move_galvo(1,1))
        self._mw.galvoDownButton.clicked.connect(lambda: self.move_galvo(1,-1))
        self._mw.galvoLeftButton.clicked.connect(lambda: self.move_galvo(0,-1))
        self._mw.galvoRightButton.clicked.connect(lambda: self.move_galvo(0,1))
        self._mw.posButton.clicked.connect(self.set_pos_mode)
        self._mw.voltButton.clicked.connect(self.set_volt_mode)
        self._mw.moveButton.clicked.connect(self.manual_move)

        # Connect spinbox
        self._mw.GalvoStepSize.valueChanged.connect(self.galvo_step_changed)

        # Connect signals
        self._galvo_logic.sig_update_display.connect(self.update_galvo_display)

        self.show()


    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()


    def move_galvo(self, axis, direction):
        """Move galvo

        Args:
            axis (int): 0->x, 1->y
            direction (int, optional): Step direction. Defaults to 1.
        """
        if self.is_pos_mode:
            self._galvo_logic._galvo.move_galvo_pos(axis, direction, self.galvo_step_size)
        else:
            self._galvo_logic._galvo.move_galvo_volt(axis, direction, self.galvo_step_size)


    def manual_move(self):
        """Manually move the galvo
        """
        position = [self._mw.xInput.value(), self._mw.yInput.value()]

        if (self.is_pos_mode):
            position[0] = position[0]
            position[1] = position[1]
            self._galvo_logic._galvo.set_position(position)
        else:
            # self._galvo_logic.set_diff_voltage(0,1,position[0])
            # self._galvo_logic.set_diff_voltage(2,3,position[1])
            self._galvo_logic._galvo.set_voltage_scaled(position)


    def galvo_step_changed(self):
        """Change the step size of the galvo
        """
        self.galvo_step_size = self._mw.GalvoStepSize.value()


    def update_galvo_display(self):
        """ Update the galvo display
        """
        self.galvo_position = self._galvo_logic.position
        self.diff_volt = self._galvo_logic.diff_volt
        self._mw.galvoXVal.setText(str(round(self.galvo_position[0]/self.um,3)))
        self._mw.galvoYVal.setText(str(round(self.galvo_position[1]/self.um,3)))
        self._mw.galvoXVolt.setText(str(round(self.diff_volt[0],3)))
        self._mw.galvoYVolt.setText(str(round(self.diff_volt[1],3)))


    def set_pos_mode(self):
        """ Set the galvo to position mode
        """
        self.is_pos_mode = True


    def set_volt_mode(self):
        """ Set the galvo to volate mode
        """
        self.is_pos_mode = False


    def show(self):
        """Make main window visible and put it above all other windows. """
        # Show the Main GUI:
        self._mw.show()
        self._mw.activateWindow()
        self._mw.raise_()
