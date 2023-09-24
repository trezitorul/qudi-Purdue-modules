# -*- coding: utf-8 -*-

"""
Hardware module for the stepper motor

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
from qudi.hardware.motor.stepper import Stepper
from qudi.core.configoption import ConfigOption


class StepperMotor (Base):
    motor_pin_1 = ConfigOption(name='motor_pin_1', missing='error')
    motor_pin_2 = ConfigOption(name='motor_pin_2', missing='error')
    motor_pin_3 = ConfigOption(name='motor_pin_3', missing='error')
    motor_pin_4 = ConfigOption(name='motor_pin_4', missing='error')
    
    def on_activate(self):
        """ On activate
        """
        pass


    def initialize(self, board):
        """Initialization of the stepper driver board

        Args:
            board (pyfirmata.Arduino): the Arduino controller board
        """
        self.board = board
        self.stepsPerRevolution = 2048
        self.rpm = 12
        self.position = 0

        self._Stepper = Stepper(self.board, self.stepsPerRevolution, self.motor_pin_1, self.motor_pin_3, self.motor_pin_2, self.motor_pin_4)
        self._Stepper.set_speed(self.rpm)


    def on_deactivate(self):
        """On deactivate
        """
        return


    def move_rel(self,  direction, step=1):
        """Moves stage in given direction (relative movement)

        Args:
            direction (int): 1 corresponds to up/right; -1 corresponds to down/left
            step (int, optional): number of steps. Defaults to 1.

        """
        self._Stepper.step(step * direction)
        self.position += step * direction


    def get_pos(self):
        """Get current position

        Returns:
            int: current position
        """
        return self.position


    def get_rpm(self):
        """ Gets the current rpm for all connected axes.

        @return int : Current rpm
        """
        return self.rpm


    def set_rpm(self, rpm):
        """Set the rpm of the motor

        Args:
            rpm (int): round-per-minute
        """
        self._Stepper.set_speed(rpm)
        self.rpm = rpm

