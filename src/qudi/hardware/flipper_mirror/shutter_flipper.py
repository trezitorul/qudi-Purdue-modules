from qudi.core.configoption import ConfigOption
from qudi.core.connector import Connector
import pyfirmata
from qudi.hardware.motor.stepper import Stepper
from qudi.interface.flipper_interface import FlipperInterface
class ShutterFlipper(FlipperInterface):
    """ Hardware module for flipper mirror, using device ID to connect.
    on - is when the beam is blocked
    """

 
    com_port = ConfigOption(name='com_port', missing='error')
    motor_pin_1 = ConfigOption(name='motor_pin_1', missing='error')
    motor_pin_2 = ConfigOption(name='motor_pin_2', missing='error')
    motor_pin_3 = ConfigOption(name='motor_pin_3', missing='error')
    motor_pin_4 = ConfigOption(name='motor_pin_4', missing='error')
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

    def on_activate(self):


        self.SetupDevice(self.com_port)
        self.HomeMirror()


    def on_deactivate(self):
        """ Deactivate modeule.
        """
        self.set_mode("on")


    def SetMode(self, mode):
        """ Sets mode of flipper mirror of specified number 'num'.
        @param (str) mode: mode to set given mirror to; must be 'on' or 'off'
        @param (int) num: number of flipper mirror that will move; either 1 or 2
        """
        dir = 0
        if mode == 'on':
            dir = 1
        elif mode =='off':
            dir = -1
        else:
            self.log.error(f"Wrong mode input") 
            return True
        self._Stepper.move_rel(dir, int(self._Stepper.stepsPerRevolution/6))
        return False

    def HomeMirror(self):
        '''
        Homes mirror.
        '''
        self.log.info("Homing Shutter")
        self._Stepper.move_rel(1, int(self._Stepper.stepsPerRevolution/2))
        self.log.info("Shutter Homing Complete")
        return

    def SetupDevice(self,com_port):
        self._Stepper = Stepper(self.com_port, 2048, self.motor_pin_1, self.motor_pin_3, self.motor_pin_2, self.motor_pin_4)
        self._Stepper.set_speed(12)
        self.log.info("Shutter on " + self.com_port + " Enabled")
        return self._Stepper
