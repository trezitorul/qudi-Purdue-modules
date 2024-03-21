# -*- coding: utf-8 -*-

"""
Hardware module for the spectrometer

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
from seabreeze.spectrometers import Spectrometer


class OzySpectrometer (Base):
    def on_activate(self):
        """ On activate
        """
        self.spec = Spectrometer.from_first_available()


    def on_deactivate(self):
        """On deactivate
        """
        return


    def set_integration_time(self,  time):
        self.spec.integration_time_micros(time)


    def get_wave_lengths(self):
        return self.spec.wavelengths()


    def get_intensities(self):
        return self.spec.intensities()
