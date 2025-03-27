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
from qtpy import QtCore

from qudi.core.configoption import ConfigOption
from qudi.core.connector import Connector
from qudi.core.module import LogicBase
from PySide2 import QtCore
from qudi.util.mutex import RecursiveMutex
from qudi.util.datastorage import TextDataStorage
from datetime import datetime
import matplotlib.pyplot as plt



class SaturationLogic(LogicBase):
    #Connectors
    VA = Connector(interface='MotorInterface')
    counter = Connector(interface='counter_logic')
    powerMeter = Connector(interface='ProcessInterface')
    OPM = Connector(interface='OpmInterface')
    _poi_manager_logic = Connector(name='poi_manager_logic', interface='PoiManagerLogic')

    counter_channels = ConfigOption(name='counter_channels', missing='error')#Channel 1 and 2 to be used for counting
    #TODO ADD Channels to measure on 
    W=1
    mW=1E-3*W
    uW=1E-3*mW
    s = 1
    ms = s*1E-3
    #Variables
    stop_requested = False
    stop_power = 2000*uW #uW
    start_power = 10*uW #uW
    initial_power = 0*uW
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
    sigStartMeasurement = QtCore.Signal()
    sigStopMeasurement = QtCore.Signal()
    sigSaveStateChanged = QtCore.Signal(bool)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thread_lock = RecursiveMutex()

    def on_activate(self):
        self._counter_logic = self.counter()
        self._OPM = self.OPM()
        self._power_meter = self.powerMeter()
        self._VA = self.VA()
        self._poi = self._poi_manager_logic()

        self.sigStartMeasurement.connect(self.start_measurement)
        self.sigStopMeasurement.connect(self.stop_measurement)

        

    @QtCore.Slot()
    def measure_saturation(self):
        self.initial_power=self.get_power()
        self.data =[]
        self.stop_requested=False
        self.set_integration_time(self.integration_time)
        #self._power_meter.set_averaging_time(self.integration_time)

        for power in np.linspace(self.start_power, self.stop_power, int(self.num_points)):
            if self.stop_requested:
                self.sigMeasurementComplete.emit()
                break
            VA_pos=self.set_power(power)
            # print("Set P")
            # print(power)
            power_data = []
            count_data = []
            for i in range(self.num_to_average):
                power_data += [self.get_power()]
                count_data += [self.get_counts()]
            # print(count_data)
            power_data = np.array(power_data).T
            count_data = np.array(count_data).T
            power_mean = np.mean(power_data) #Scalar
            count_mean = np.mean(count_data, axis = 1) #List
            power_std  = np.std(power_data, axis=0)#Scalar
            count_std  = np.std(count_data, axis=1)#List
            self.data += [np.hstack(([VA_pos, power_mean, power_std], np.ravel(np.column_stack([count_mean, count_std])))).tolist()]#stack and ravel interleaves the values
            self.sigUpdateDisplay.emit()
        self.log.info("Completed Saturation Measurement, returning laser to: " + str(self.initial_power) + " uW")
        self.set_power(self.initial_power*self.uW)
        print("SETTING POWER")
        self.sigMeasurementComplete.emit()
        self.sigStopMeasurement.emit()

    @QtCore.Slot()
    def initiate_measurement(self):

        self.sigStartMeasurement.emit()

    def start_measurement(self):
        self.stop_requested=False
        self._OPM.g2_mode()
        self.measure_saturation()

    @QtCore.Slot()
    def halt_measurement(self):
        self.stop_requested=True
        self.sigStopMeasurement.emit()
        self._OPM.camera_mode()

    @QtCore.Slot()
    def stop_measurement(self):
        # print("Stopping Measurement")

        with self._thread_lock:
            if self.module_state() == 'locked':
                # print("Unlocking M")
                self.module_state.unlock()

    def configure_scan(self, start_power, stop_power, num_points, integration_time, num_to_average):#Input in units of uW
        self.start_power= start_power*self.uW
        self.stop_power = stop_power*self.uW
        self.num_points = num_points
        self.integration_time = integration_time*self.ms
        self.num_to_average = num_to_average

    def set_power(self, power):#Power set in uW
        power = power/self.uW #Convert to W for calculations
        rel_tol = 0.05 #Percentage off the power can be to account for limited resolution of linear actuator.
        curr_power = self.get_power()
        error = abs(power-curr_power)
        step_delay_time = 0.1
        max_attempts = 300
        step_size = 0.1
        position = self.get_VA_position()

        for _ in range(max_attempts):
            power_achieved=False
            # print("STOP REQUESTED")
            # print(self.stop_requested)
            if self.stop_requested:
                # print("Stop Requested, stopping set power process")
                self.sigMeasurementComplete.emit()
                break
            curr_power = self.get_power()
            error = power - curr_power
            # print("CP")
            # print(curr_power)
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
            
            if position >=99:
                self.log.error("LAVA MAX SETPOINT REACHED SET POWER NOT ACHIEVABLE")
                return False

            self.set_VA_position(position)
            time.sleep(step_delay_time)
        self.log.error("FAILED TO ACHIEVE REQUESTED POWER: " + str(power) + " Final Power Achieved: " + str(curr_power))
        self.halt_measurement()
        # print("Final Position Reached, desired power: " + str(power) + ", Actual Power Achieved: " + str(curr_power))
        #return position


    def get_power(self): #Should return in units of Watts
        #return self.VA_POS*2*self.uW
        return self._power_meter.get_process_value()
    def get_counts(self):
        return self._counter_logic.get_count_rates(self.counter_channels)
    def set_integration_time(self, dT):
        self._counter_logic.set_exposure_time(dT)
    def set_VA_position(self, position):
        #self.VA_POS = position
        self._VA.move_abs(position)
    def get_VA_position(self):
        #return self.VA_POS
        position = self._VA.get_pos()
        if type(position)==float:
            self.VA_POS=position
            return position
        else:
            return position
    def on_deactivate(self):
        pass
    
    def initiate_save(self):
        print("Initating Saturation Data Save")
        self.save(self.data)

    def plot_data(self, data, title=None):
        fig, ax = plt.subplots()
        num_channel=1
        print(data)
        
        print(data[1])

        for counter in self.counter_channels:
            print(data[2*num_channel+1])
            ax.plot(data[1], data[2*num_channel+1], label=counter)
            num_channel+=1
        ax.set_xlabel("Power (uW)")
        ax.set_ylabel("Count Rate (cps)")
        if title is not None:        # Y-axis label
            ax.set_title(title)  # Title
        else:
            ax.set_title("Saturation Measurement")
        ax.legend()
        return fig

    def save(self, scan_data):
        print("TEST1")
        print(self.module_state())
        with self._thread_lock:
            if self.module_state() != 'idle':
                self.log.error('Unable to save Saturation Data. Saving still in progress...')
                return

            if scan_data is None:
                self.log.error('Unable to save Saturation Data. No data available.')
                raise ValueError('Unable to save Saturation Data. No data available.')

            self.sigSaveStateChanged.emit(True)
            self.module_state.lock()

            try:
                ds = TextDataStorage(root_dir=self.module_default_data_dir)

                timestamp = datetime.now()
                # ToDo: Add meaningful metadata if missing:
                parameters = {}
                parameters["Start Power"] = self.start_power
                parameters["Start Power Units"]="W"
                parameters["Stop Power"] =  self.stop_power
                parameters["Stop Power Units"]="W"
                parameters["Number of Scan Points"] = self.num_points
                parameters["Number of Averages per Scan Point"] = self.num_to_average
                parameters["Intensities"] = "Intensities"
                parameters["Intensity Units"] = "CPS"
                tag="Saturation Measurement"

                if self._poi_manager_logic().active_POI_Visible():
                    parameters["ROI"]=self._poi_manager_logic().roi_name
                    parameters["POI"]=self._poi_manager_logic().active_poi
                    tag = "Saturation Measurement of "+str(parameters["ROI"]+", "+str(parameters["POI"]))
                print("TEST3+++++++++++++++++++++++++++++++++++")
                self.np_data=np.asarray(scan_data)
                column_headers='VA Position;;Power Mean(uW);;Power Standard Deviation (uW)'
                for counter in self.counter_channels:
                    column_headers = column_headers+";;"+counter +" Mean Intensity (cps);;"+ counter + " Intensity Standard Deviation (cps)"
                print("Column Headers")
                file_path, _, _ = ds.save_data(self.np_data,
                                                   metadata=parameters,
                                                   nametag=tag,
                                                   timestamp=timestamp,
                                                   column_headers=column_headers)
                    # thumbnail

                figure = self.plot_data(self.np_data.T, tag)
                ds.save_thumbnail(figure, file_path=file_path.rsplit('.', 1)[0])

            finally:
                self.log.info("Saturation Data Saved at: " + str(file_path))
                self.module_state.unlock()
                self.sigSaveStateChanged.emit(False)
            return