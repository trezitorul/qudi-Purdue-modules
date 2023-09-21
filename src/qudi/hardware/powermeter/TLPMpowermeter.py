# -*- coding: utf-8 -*-
"""
Thorlabs PM100D powermeter hardware module. Must have address to activate, does not use visa resource manager.

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
import numpy as np

from qudi.core.module import Base
from qudi.core.configoption import ConfigOption

from qudi.interface.simple_data_interface import SimpleDataInterface
from qudi.interface.process_interface import ProcessInterface

from qudi.hardware.powermeter.TLPM import TLPM

from datetime import datetime
from ctypes import cdll,c_long, c_ulong, c_uint32,byref,create_string_buffer,c_bool,c_char_p,c_int,c_int16,c_double, sizeof, c_voidp
import time


class PowerMeter(SimpleDataInterface, ProcessInterface):
    """ Hardware module for Thorlabs PM100D powermeter using TLPM.

    Example config :
    powermeter:
        module.Class: 'powermeter.TLPMpowermeter.PowerMeter'
        address: 'USB0::0x1313::0x8078::P0013645::INSTR'
    """

    _address = ConfigOption('address', missing='error')
    _timeout = ConfigOption('timeout', 1)
    _power_meter = None

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        IDQuery = True
        resetDevice = True
        self.tlPM = TLPM()
        self.deviceCount = c_uint32()
        self.tlPM.findRsrc(byref(self.deviceCount))

        # print("Number of found devices: " + str(self.deviceCount.value))
        # print("")

        self.resourceName = create_string_buffer(1024)

        for i in range(0, self.deviceCount.value):
            self.tlPM.getRsrcName(c_int(i), self.resourceName)
            # print("Resource name of device", i, ":", c_char_p(self.resourceName.raw).value)
        # print("")
        self.tlPM.close()
        i=0
        if i not in range(0, self.deviceCount.value):
            print(f"Device index {i} out of range [0,{self.deviceCount.value}]")
        else:
            self.tlPM.getRsrcName(c_int(i), self.resourceName)
            self.tlPM.open(self.resourceName, c_bool(IDQuery), c_bool(resetDevice))

            message = create_string_buffer(1024)
            self.tlPM.getCalibrationMsg(message)
            # print("Connected to device", i)
            # print("Last calibration date: ",c_char_p(message.raw).value)
            # print("")

            time.sleep(1) #minimize?
        
        self.power = 0


    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module.
        """
        self.tlPM.close()

    def getData(self):
        """ SimpleDataInterface function to get the power from the powermeter """
        return np.array([self.get_power()])

    def getChannels(self):
        """ SimpleDataInterface function to know how many data channel the device has, here 1. """
        return 1

    def get_power(self):
        """ Return the power read from the ThorlabsPM100 package 
        @return (float): power output in mW
        """
        power =  c_double()
        self.tlPM.measPower(byref(power))
        self.power = power.value *10**6

        return self.power

    def get_process_value(self):
        """ SimpleDataInterface function to return a measured value.
        @return (float): power output in mW
        """
        return self.get_power()

    def get_process_unit(self):
        """ Return the unit that the value is measured in as a tuple of ('abreviation', 'full unit name') 
        @return (tuple): units of value
        """
        return ('mW', 'milliwatt')

    def get_wavelength(self):
        """ Return the current wavelength in nanometers. NOT USED
        @return (float): wavelength
        """
        return self._power_meter.sense.correction.wavelength

    def set_wavelength(self, value=None):
        """ Set the new wavelength in nanometers
        @param (float) value: wavelength 
        """
        self.tlPM.setWavelength(c_double(value))

    def get_wavelength_range(self):
        """ Return the wavelength range of the power meter in nanometers. NOT USED
        @return (float): wavelength range
        """
        return self._power_meter.sense.correction.minimum_beamdiameter,\
               self._power_meter.sense.correction.maximum_wavelength

