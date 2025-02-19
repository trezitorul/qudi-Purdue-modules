# -*- coding: utf-8 -*-
"""
Saturation Measurement Module, moves the LAVA, measures the count rate, and the power

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

import time
import numpy as np

from qudi.core.configoption import ConfigOption
from qudi.core.connector import Connector
from qudi.core.module import LogicBase
from PySide2 import QtCore
from qudi.util.mutex import RecursiveMutex


class SaturationLogic(LogicBase):
    #Connectors
    VA = Connector(interface='MotorInterface')
    counter = Connector(interface='counter_logic')
    powerMeter = Connector(interface='ProcessInterface')
    OPM = Connector(interface='OpmInterface')

    counter_channels = ConfigOption(name='counter_channels', missing='error')#Channel 1 and 2 to be used for counting
    #TODO ADD Channels to measure on 
    W=1
    mW=1E-3*W
    uW=1E-3*mW
    #Variables
    stop_requested = False
    stop_power = 2000*uW #uW
    start_power = 10*uW #uW
    integration_time = 0.001 #sec
    num_to_average = 1
    data = [] #Format is 
    #data[0] is the LAC Position,
    #data[1] is the measured power, 
    #data[2] is measured power instability, 
    #data[3] is measured count rate, 
    #data[4] is measured count rate instability
    channels =[]
    VA_POS=0

    #Signals
    sigMeasurementComplete = QtCore.Signal()
    queryInterval = ConfigOption('query_interval', 100)
    sigUpdateDisplay = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_activate(self):
        self._counter_logic = self.counter()
        self._OPM = self.OPM()
        self._power_meter = self.powerMeter()
        self._VA = self.VA()
        

    def start_measurement(self):
        self.data =[]
        self.stop_requested=False
        self.set_integration_time(self.integration_time)
        #self._power_meter.set_averaging_time(self.integration_time)

        for power in np.linspace(self.start_power, self.stop_power, int(self.num_points)):
            VA_pos=self.set_power(power)
            print("Set P")
            print(power)
            power_data = []
            count_data = []
            for i in range(self.num_to_average):
                power_data += [self.get_power()]
                count_data += [self.get_counts()]
            print(count_data)
            power_data = np.array(power_data).T
            count_data = np.array(count_data).T
            power_mean = np.mean(power_data) #Scalar
            count_mean = np.mean(count_data, axis = 1) #List
            power_std  = np.std(power_data, axis=0)#Scalar
            count_std  = np.std(count_data, axis=1)#List
            self.data += [np.hstack(([VA_pos, power_mean, power_std], np.ravel(np.column_stack([count_mean, count_std])))).tolist()]#stack and ravel interleaves the values
            print(self.data)

            self.sigUpdateDisplay.emit()

    def stop_measurement(self):
        self.stop_requested=True

    def configure_scan(self, start_power, stop_power, num_points, integration_time, num_to_average):#Input in units of uW
        self.start_power= start_power*self.uW
        self.stop_power = stop_power*self.uW
        self.num_points = num_points
        self.integration_time = integration_time
        self.num_to_average = num_to_average

    def set_power(self, power):#Power set in uW
        power = power #Convert to W for calculations
        rel_tol = 0.05 #Percentage off the power can be to account for limited resolution of linear actuator.
        curr_power = self.get_power()
        error = abs(power-curr_power)
        step_delay_time = 0.1
        max_attempts = 100
        step_size = 1
        position = self.get_VA_position()
        for _ in range(max_attempts):
            curr_power = self.get_power()
            error = power - curr_power
            # print("CP")
            # print(curr_power/self.uW)
            # print("SP")
            # print(power/self.uW)
            # print("E")
            # print(error)
            # print("POS")
            # print(position)
            # print("VA")
            # print(self.VA_POS)
            if abs(error) <= rel_tol*power:

                return position

            if error > 0:
                position = position + step_size
            else:
                position = position - step_size
            
            # if position >=99:
            #     self.log.error("LAVA MAX SETPOINT REACHED SET POWER NOT ACHIEVABLE")
            #     return False

            self.set_VA_position(position)
            time.sleep(step_delay_time)

        print("Final Position Reached, desired power: " + str(power) + ", Actual Power Achieved: " + str(curr_power))
        return position


    def get_power(self): #Should return in units of Watts
        return self.VA_POS*2*self.uW
        #return self._power_meter.get_process_value()
    def get_counts(self):
        return self._counter_logic.get_count_rates(self.counter_channels)
    def set_integration_time(self, dT):
        self._counter_logic.set_exposure_time(dT)
    def set_VA_position(self, position):
        self.VA_POS = position
        #self._VA.move_abs(position)
    def get_VA_position(self):
        return self.VA_POS
        #return self._VA.get_pos()
    def on_deactivate(self):
        pass
    