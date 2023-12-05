# -*- coding: utf-8 -*-

"""

Flipper mirror hardware module using Thorlabs Motion Control DLLs.

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

import os
import time
import logging
import sys
import clr
# import matplotlib.pyplot as plt
# from scipy import signal
from qudi.core.configoption import ConfigOption
from qudi.interface.flipper_interface import FlipperInterface
import numpy as np
from ctypes import *
# from System import Decimal

sys.path.append(r"C:\\Program Files\\Thorlabs\\Kinesis")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.FilterFlipperCLI.dll")
clr.AddReference("System.Collections")
clr.AddReference("System.Linq")

from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI 
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceNotReadyException 
from Thorlabs.MotionControl.FilterFlipperCLI import FilterFlipper

class FlipperMirror(FlipperInterface):
    """ Hardware module for flipper mirror, using device ID to connect.
    """

    _deviceID = ConfigOption(name='deviceID', missing='error')

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        self.deviceID = self._deviceID
        try:
            self._FlipperMirror = self.SetupDevice(self.deviceID)
            self.log.info(f"deviceID: {self.deviceID} connected")
            self.HomeMirror()
        except Exception as e:
            self.log.info(f"deviceID: {self.deviceID} failed to connect")
            self.log.error(e)
    
        # Reset the flipper
        # self.SetMode("on")    
    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module.
        """
        self.device.StopPolling()
        self.device.Disconnect(True)

    
    def SetupDevice(self,deviceID):
        '''
        Create flipper mirror object.
        @param (int) deviceID: serial number of flipper mirror to be used
        '''
        DeviceManagerCLI.BuildDeviceList()

        self.device = FilterFlipper.CreateFilterFlipper(str(deviceID))

        self.device.Connect(deviceID)
        self.device.StartPolling(250)
        time.sleep(0.25)
        self.device.EnableDevice()
        time.sleep(0.25)
        return self.device

    def SetMode(self,mode):
        '''
        Turn the mirror 90 degrees relative to the main body (on) or 0 degree (off)
        @param (str) mode: mode to set mirror to; must be 'on' or 'off'
        '''
        if mode == 'on':
            self.device.SetPosition(2,60000)
        elif mode == 'off':
            self.device.SetPosition(1,60000)
        else:
            print('wrong mode, try again')
        return
    
    def HomeMirror(self):
        '''
        Homes mirror.
        '''
        self.device.Home(60000)
        return
'''
basic demo
'''
#deviceID = "37005466"
#Mirror = MFF101FlipperMirror(deviceID)
#Mirror.HomeMirror()
#Mirror.SetMode("on")