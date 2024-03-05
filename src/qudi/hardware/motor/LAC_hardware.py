# -*- coding: utf-8 -*-

"""
LAC hardware module using motor interface and process control interface (for PID).

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

from PyQt5.QtCore import QObject
from qudi.interface.motor_interface import MotorInterface
from qudi.interface.process_control_interface import ProcessControlInterface
from qudi.hardware.motor.LAC_class import LAC


class LACHardware(MotorInterface, ProcessControlInterface):
    
    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        self._LAC = LAC()

        # Reset the LAC
        self._LAC.reset()
        self._LAC.set_accuracy(value=0)
        self._LAC.set_movement_threshold(value=0)
        self._LAC.set_proportional_gain(100)
        self._LAC.set_derivative_gain(1)

        # Set position to last position?
        # self.position = self.get_pos()
        self.position = 99


    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module.
        """
        pass


    def move_abs(self, position):
        """ Moves stage to absolute position (absolute movement)

        The value you want to send is calculated by (distance * 1023)/stroke
        where distance is intended distance and stroke is max extension length, 
        all values in mm. Round to nearest integer

        @param (int) setPos: position to set stage to. 0 -> 100

        @return int: error code (0:OK, -1:error)
        """
        #print(str(int(position / 100 * 1023)))
        self._LAC.set_position(int(position / 100 * 1023))

        return 0


    def get_pos(self, param_list=None):
        """ Gets current position of the stage arms

        @param list param_list: optional, if a specific position of an axis
                                is desired, then the labels of the needed
                                axis should be passed in the param_list.
                                If nothing is passed, then from each axis the
                                position is asked.

        @return (float) self.position: position of dummy LAC
        """
        position = self._LAC.get_feedback()
        
        if (position is not None):
            self.position = position / 1023 * 100
        
        return self.position


    def set_control_value(self, value, channel=None):
        """ Set the value of the controlled process variable

        @param (float) value: The value to set
        @param (int) channel: (Optional) The number of the channel

        """
        self.move_abs(value)


    def get_control_value(self, channel=None):
        """ Get the value of the controlled process variable

        @param (int) channel: (Optional) The number of the channel

        @return (float): The current control value
        """
        return self.get_pos()


    def get_control_unit(self, channel=None):
        """ Return the unit that the value is set in as a tuple of ('abbreviation', 'full unit name')

        NOT IMPLEMENTED FOR LAC

        @param (int) channel: (Optional) The number of the channel

        @return: The unit as a tuple of ('abbreviation', 'full unit name')
        """
        pass

    def get_control_limit(self, channel=None):
        """ Return limits within which the controlled value can be set as a tuple of (low limit, high limit)

        @param (int) channel: (Optional) The number of the channel

        @return (tuple): The limits as (low limit, high limit)
        """
        return (0, 99)


    def process_control_get_number_channels(self):
        """ Function to get the number of channels available for control

        @return (int): The number of controllable channel(s)

        This function is not abstract - Thus it is optional and if a hardware do not implement it, the answer is 1.
        """
        pass


    def get_constraints(self):
        """ Retrieve the hardware constrains from the motor device.

        NOT IMPLEMENTED FOR LAC

        @return dict: dict with constraints for the magnet hardware. These
                      constraints will be passed via the logic to the GUI so
                      that proper display elements with boundary conditions
                      could be made.

        Provides all the constraints for each axis of a motorized stage
        (like total travel distance, velocity, ...)
        Each axis has its own dictionary, where the label is used as the
        identifier throughout the whole module. The dictionaries for each axis
        are again grouped together in a constraints dictionary in the form

            {'<label_axis0>': axis0 }

        where axis0 is again a dict with the possible values defined below. The
        possible keys in the constraint are defined here in the interface file.
        If the hardware does not support the values for the constraints, then
        insert just None. If you are not sure about the meaning, look in other
        hardware files to get an impression.

        Example of how a return dict with constraints might look like:
        ==============================================================

        constraints = {}

        axis0 = {}
        axis0['label'] = 'x'    # it is very crucial that this label coincides
                                # with the label set in the config.
        axis0['unit'] = 'm'     # the SI units, only possible m or degree
        axis0['ramp'] = ['Sinus','Linear'], # a possible list of ramps
        axis0['pos_min'] = 0,
        axis0['pos_max'] = 100,  # that is basically the traveling range
        axis0['pos_step'] = 100,
        axis0['vel_min'] = 0,
        axis0['vel_max'] = 100,
        axis0['vel_step'] = 0.01,
        axis0['acc_min'] = 0.1
        axis0['acc_max'] = 0.0
        axis0['acc_step'] = 0.0

        axis1 = {}
        axis1['label'] = 'phi'   that axis label should be obtained from config
        axis1['unit'] = 'degree'        # the SI units
        axis1['ramp'] = ['Sinus','Trapez'], # a possible list of ramps
        axis1['pos_min'] = 0,
        axis1['pos_max'] = 360,  # that is basically the traveling range
        axis1['pos_step'] = 100,
        axis1['vel_min'] = 1,
        axis1['vel_max'] = 20,
        axis1['vel_step'] = 0.1,
        axis1['acc_min'] = None
        axis1['acc_max'] = None
        axis1['acc_step'] = None

        # assign the parameter container for x to a name which will identify it
        constraints[axis0['label']] = axis0
        constraints[axis1['label']] = axis1
        """
        pass


    def move_rel(self,  param_dict):
        """ Moves stage in given direction (relative movement)

        @param dict param_dict: dictionary, which passes all the relevant
                                parameters, which should be changed. Usage:
                                 {'axis_label': <the-abs-pos-value>}.
                                 'axis_label' must correspond to a label given
                                 to one of the axis.

        A smart idea would be to ask the position after the movement.

        @return int: error code (0:OK, -1:error)
        """
        pass


    def abort(self):
        """ Stops movement of the stage

        @return int: error code (0:OK, -1:error)
        """
        return 0


    def get_status(self, param_list=None):
        """ Get the status of the position

        NOT IMPLEMENTED

        @param list param_list: optional, if a specific status of an axis
                                is desired, then the labels of the needed
                                axis should be passed in the param_list.
                                If nothing is passed, then from each axis the
                                status is asked.

        @return dict: with the axis label as key and the status number as item.
        """
        pass


    def calibrate(self, param_list=None):
        """ Calibrates the stage.

        NOT IMPLEMENTED

        @param dict param_list: param_list: optional, if a specific calibration
                                of an axis is desired, then the labels of the
                                needed axis should be passed in the param_list.
                                If nothing is passed, then all connected axis
                                will be calibrated.

        @return int: error code (0:OK, -1:error)

        After calibration the stage moves to home position which will be the
        zero point for the passed axis. The calibration procedure will be
        different for each stage.
        """
        pass


    def get_velocity(self, param_list=None):
        """ Gets the current velocity for all connected axes.

        NOT IMPLEMENTED

        @param dict param_list: optional, if a specific velocity of an axis
                                is desired, then the labels of the needed
                                axis should be passed as the param_list.
                                If nothing is passed, then from each axis the
                                velocity is asked.

        @return dict : with the axis label as key and the velocity as item.
        """
        pass


    def set_velocity(self, param_dict):
        """ Write new value for velocity.

        NOT IMPLEMENTED

        @param dict param_dict: dictionary, which passes all the relevant
                                parameters, which should be changed. Usage:
                                 {'axis_label': <the-velocity-value>}.
                                 'axis_label' must correspond to a label given
                                 to one of the axis.

        @return int: error code (0:OK, -1:error)
        """
        pass
