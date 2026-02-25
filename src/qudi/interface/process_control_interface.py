# -*- coding: utf-8 -*-

"""
Interface file to control processes in PID control.

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

from abc import abstractmethod
from qudi.core.module import Base


class ProcessControlInterface(Base):
    """ A simple interface to control one or multiple process value.

    This interface is in fact a very general/universal interface that can be used for a lot of things.
    It can be used to interface any hardware where one to control one or multiple control value, like a temperature
    or how much a PhD student get paid.
    """

    @abstractmethod
    def set_control_value(self, value, channel=None):
        """ Set the value of the controlled process variable

        :param float value: The value to set
        :param int,optional channel: The number of the channel

        """
        pass

    @abstractmethod
    def get_control_value(self, channel=None):
        """ Get the value of the controlled process variable

        :param int,optional channel: The number of the channel
        :returns: The current control value
        :rtype: float
        """
        pass

    @abstractmethod
    def get_control_unit(self, channel=None):
        """ Return the unit that the value is set in as a tuple of ('abbreviation', 'full unit name')

        :param int,optional channel: The number of the channel

        :returns: The unit as a tuple of ('abbreviation', 'full unit name')
        :rtype: tuple
        """
        pass

    @abstractmethod
    def get_control_limit(self, channel=None):
        """ Return limits within which the controlled value can be set as a tuple of (low limit, high limit)

        :param int,optional channel: The number of the channel

        :returns: The limits as (low limit, high limit)
        :rtype: tuple
        """
        pass

    def process_control_supports_multiple_channels(self):
        """ Function to test if hardware support multiple channels

        :returns: Whether the hardware supports multiple channels
        :rtype: bool

        This function is not abstract - Thus it is optional and if a hardware do not implement it, the answer is False.
        """
        return False

    def process_control_get_number_channels(self):
        """ Function to get the number of channels available for control

        :returns: The number of controllable channel(s)
        :rtype: int

        This function is not abstract - Thus it is optional and if a hardware do not implement it, the answer is 1.
        """
        return 1
