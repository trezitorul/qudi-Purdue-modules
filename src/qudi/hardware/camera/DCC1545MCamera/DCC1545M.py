# -*- coding: utf-8 -*-

"""
This hardware module implement the camera interface to use a Thorlabs Camera.
It use a dll to inteface with the instruments via USB (only available physical interface)

---

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

import platform
import ctypes
from ctypes import *

import numpy as np

from qudi.core.module import Base
from qudi.interface.camera_interface import CameraInterface
from qudi.hardware.camera.DCC1545MCamera.uc480 import uc480


class DCC1545M(CameraInterface):

    def on_activate(self):
        self.camera = uc480()
        self.camera.connect()

    
    def on_deactivate(self):
        self.stop_acquisition()
        self.camera.disconnect()


    def get_name(self):
        return(str(self.camera._camID))


    def get_size(self):
        """ Retrieve size of the image in pixel

        @return tuple: Size (width, height)
        """
        return self.camera.get_sensor_size()


    def support_live_acquisition(self):
        """ Return whether or not the camera can take care of live acquisition

        @return bool: True if supported, False if not
        """
        return True

    def start_live_acquisition(self):
        """ Start a continuous acquisition

        @return bool: Success ?
        """
        img = self.camera.acquire(5)
        return (img != None)



    def start_single_acquisition(self):
        """ Start a single acquisition

        @return bool: Success ?
        """
        return self.start_single_acquisition()


    def stop_acquisition(self):
        """ Stop/abort live or single acquisition

        @return bool: Success ?
        """
        return True


    def get_acquired_data(self):
        """ Return an array of last acquired image.

        @return numpy array: image data in format [[row],[row]...]

        Each pixel might be a float, integer or sub pixels
        """
        # Number of acquired frames to average. Needs to be > 1
        return self.camera.acquire(3)
        


    def set_exposure(self, exposure):
        """ Set the exposure time in seconds

        @param float exposure: desired new exposure time

        @return float: setted new exposure time
        """
        self.camera.set_exposure(exposure)
        return self.get_exposure()


    def get_exposure(self):
        """ Get the exposure time in seconds

        @return float exposure time
        """
        return self.camera.get_exposure()


    def set_gain(self, gain):
        """ Set the gain

        @param float gain: desired new gain

        @return float: new exposure gain
        """
        self.camera.set_gain(gain)
        return self.get_gain()


    def get_gain(self):
        """ Get the gain

        @return float: exposure gain
        """
        return self.camera.get_gain()


    def get_ready_state(self):
        """ Is the camera ready for an acquisition ?

        @return bool: ready ?
        """
        return self.camera._is_open
