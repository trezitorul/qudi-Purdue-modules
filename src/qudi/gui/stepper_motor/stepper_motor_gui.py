import os

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qtpy import QtWidgets
from qtpy import uic
from qtpy.QtCore import QTimer, Signal
from qtpy.QtCore import QTimer, Qt, QEvent



class StepperMainWindow(QtWidgets.QMainWindow):
    """ Create the Main Window based on the *.ui file. """

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'ui_stepper_motor.ui')

        # Load it
        super().__init__()
        uic.loadUi(ui_file, self)
        self.show()


class StepperGUI(GuiBase):
    """

    """
    
    # CONNECTORS #############################################################
    stepper_logic = Connector(interface='StepperMotorLogic')

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()
        #return 0

    def on_activate(self):
        """ 

        """

        # CONNECTORS PART 2 ###################################################
        self._stepper_logic = self.stepper_logic()

        self._mw = StepperMainWindow()

        # Set default parameters
        self.position = [0, 0, 0]
        self._mw.StepSize.setValue(1)
        self.step_size = 2048
        self.direction = 1
        self.axis = 0

        self._mw.rpmInput.setValue(12)
        self.rpm = 12

        # Connect buttons to functions        
        self._mw.StepSize.valueChanged.connect(self.step_changed)
        self._mw.rpmInput.valueChanged.connect(self.rpm_changed)

        self._mw.leftButton.installEventFilter(self)  # Install event filter on the button
        self._mw.leftButton.clicked.connect(lambda: self.on_button_clicked(0, -1))

        self._mw.rightButton.installEventFilter(self)  # Install event filter on the button
        self._mw.rightButton.clicked.connect(lambda: self.on_button_clicked(0, 1))

        self._mw.upButton.installEventFilter(self)  # Install event filter on the button
        self._mw.upButton.clicked.connect(lambda: self.on_button_clicked(1, 1))

        self._mw.downButton.installEventFilter(self)  # Install event filter on the button
        self._mw.downButton.clicked.connect(lambda: self.on_button_clicked(1, -1))

        self.mouse_held = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_mouse_hold)

        # Connect update signal
        self._stepper_logic.sig_update_display.connect(self.update_display)
        self.show()

    def event_filter(self, obj, event):
        """ Filter button clicked or held

        Args:
            obj (idk): object being pressed/clicked
            event (idk): event that is happening

        Returns:
            event_filter: recursively check pressed/clicked
        """
        if (obj == self._mw.leftButton or obj == self._mw.rightButton
            or obj == self._mw.upButton or obj == self._mw.downButton) and event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                self.mouse_held = True
                self.timer.start(150)  # Start the timer

        elif (obj == self._mw.leftButton or obj == self._mw.rightButton
            or obj == self._mw.upButton or obj == self._mw.downButton) and event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.LeftButton:
                self.mouse_held = False
                self.timer.stop()  # Stop the timer

        return self._mw.event_filter(obj, event)


    def check_mouse_hold(self):
        """Check if the mouse is being held
        """
        if self.mouse_held:
            self.move(self.axis, self.direction)


    def on_button_clicked(self, axis, direction):
        """ Move the stepper motors when the button is clicked

        Args:
            axis (int): 01 -> xy
            direction (int): 1 for up/right; -1 for down/left
        """
        self.move(axis, direction)
        self.axis = axis
        self.direction = direction


    def move(self, axis, direction):
        """Move the motors

        Args:
            axis (int): 01 -> xy
            direction (int): 1 for up/right; -1 for down/left
        """
        self._stepper_logic.move_rel(axis, direction, self.step_size)


    def step_changed(self):
        """ When new step size value is input
        """
        self.step_size = int(self._mw.StepSize.value() * 2048)


    def rpm_changed(self):
        """ Change the rpm speed
        """
        self.rpm = self._mw.rpmInput.value()
        self._stepper_logic.setRPM(self.rpm)


    def update_display(self):
        """Update the display
        """
        self.position_X = self._stepper_logic.position[0]
        self.position_Y = self._stepper_logic.position[1]
        self._mw.totalStepX.setText(str(self.position_X / 2048))
        self._mw.totalStepY.setText(str(self.position_Y / 2048))


    def show(self):
        """Make main window visible and put it above all other windows. """
        # Show the Main GUI:
        self._mw.show()
        self._mw.activateWindow()
        self._mw.raise_()
