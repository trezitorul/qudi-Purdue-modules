# -*- coding: utf-8 -*-

"""
Hardware module for the polarization motor

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

from qudi.core.module import Base
from qudi.core.configoption import ConfigOption

import time
import sys
import clr
from ctypes import *

sys.path.append(r"C:\\Program Files\\Thorlabs\\Kinesis")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.KCube.DCServoCLI.dll")
clr.AddReference("System.Collections")
clr.AddReference("System.Linq")
clr.AddReference('System')

from System import Decimal
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI 
from Thorlabs.MotionControl.GenericMotorCLI import GenericMotorCLI
from Thorlabs.MotionControl.KCube.DCServoCLI import KCubeDCServo

class PolarizationMotor(Base):
    """ Hardware module for polarization motor.
    """
    device_ID = ConfigOption(name='deviceID', missing='error')
    max_velocity = ConfigOption(name='maxvelocity', missing='error')


    def on_activate(self):
        """ On activation of the module
        """
        self._device_ID = self.device_ID
        self._max_velocity = self.max_velocity
        
        self.position = 0
        self.polar_motor = self.setup_device(self._device_ID)

        self.home_motor()
        self.set_velocity(self._max_velocity)

        _threaded=True
        
    
    def on_deactivate(self):
        """ When the module is deactivated
        """
        pass


    def setup_device(self,device_ID):
        """ Setting up the device

        Args:
            device_ID (str): device ID

        Returns:
            KCubeDCServo.CreateKCubeDCServo: the polar motor object
        """
        DeviceManagerCLI.BuildDeviceList()
        self.device = KCubeDCServo.CreateKCubeDCServo(self.device_ID)
        self.device.Connect(self.device_ID)
        self.device.StartPolling(1)
        time.sleep(0.25)
        self.device.EnableDevice()
        time.sleep(0.25)
        self.config = self.device.LoadMotorConfiguration(device_ID)
        self.config.DeviceSettingsName = "MTS25"
        self.config.UpdateCurrentConfiguration()

        return self.device


    def set_position(self, degree):
        """ Turn the motor to the desired degree

        Args:
            degree (float): desired degree
        """
        self.device.MoveTo(Decimal(float(degree)), 10000)
        self.position = Decimal.ToDouble(self.device.Position)

    
    def get_position(self):
        """Get the current angle

        Returns:
            float: current angle
        """
        return Decimal.ToDouble(self.device.Position)


    def home_motor(self):
        """ Home the motor
        """
        self.device.Home(60000)

    
    def set_velocity(self, max_velocity):
        """Set the velocity of the motor

        Args:
            max_velocity (float): max velocity
        """
        velparams = self.device.GetVelocityParams()
        velparams._Max_Velocity = Decimal(float(max_velocity))
        self.device.SetVelocityParams(velparams)
