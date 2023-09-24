# -*- coding: utf-8 -*-
""" Hardware module for the DAQ
"""

from mcculw import ul
from mcculw.enums import CounterChannelType
from mcculw.device_info import DaqDeviceInfo
from mcculw.enums import ULRange
from mcculw.ul import ULError
import time
from pylab import *

# from core.configoption import ConfigOption
# from core.connector import Connector
# from logic.generic_logic import GenericLogic
# from qtpy import QtCore

from qudi.core.module import Base
from qudi.core.configoption import ConfigOption


class DAQ(Base):
    """ DAQ Class. Extends from Base

    """
    range = ConfigOption(name='range', missing='error')
    mode = ConfigOption(name='mode', missing='error')

    def on_activate(self):
        """ Initialisation performed during activation of the module.
         """
        self.board_num = 0
        self.mode=self.mode
        if self.range == "BIP10VOLTS":
            self.range=ULRange.BIP10VOLTS

        channel_X_high = [0,0] #[out channel, in channel]
        channel_X_low = [1,1]
        channel_Y_high = [2,2]
        channel_Y_low = [3,3]

        self.set_mode(self.mode)


    def on_deactivate(self):
        """
        Deinitialisation performed during deactivation of the module.
        """
        self.set_zero()
        # pass


    def set_mode(self,mode):
        '''
        Set the DAQ card to either "differential" or "single_ended"
        '''
        if mode == "differential":
            ul.a_input_mode(self.board_num, 0)
            self.mode = mode
            return 
        elif mode == "single_ended":
            ul.a_input_mode(self.board_num, 1)
            self.mode = mode
            return 
        else:
            print("error, please use either differential or single_ended")
            return "null"
    

    def get_voltage(self,channel_in):
        '''
        Return analog input channel's voltage
        '''
        value_in = ul.a_in(self.board_num, channel_in, self.range)
        voltage = ul.to_eng_units(self.board_num, self.range, value_in)

        return voltage
    

    def set_voltage(self,channel_out,voltage):
        '''
        Set the analog output channel's voltage
        '''
        voltage_pk = 10
        if abs(voltage) > abs(voltage_pk):
            print("invalid voltage on" + str(channel_out)+" of " + str(voltage) + "please reenter correct voltage")
            return
        else:
            volt_value=ul.from_eng_units(self.board_num, self.range, voltage)
            value_out = ul.a_out(self.board_num, channel_out, self.range,volt_value)
            return


    def set_diff_voltage(self,channel_high, channel_low, voltage):
        '''
        Set the analog output differential voltage between 2 channel
        '''
        #print("VOLTAGE REQUESTED")
        #print(voltage)
        voltage_pk = 20
        if abs(voltage) > abs(voltage_pk):
            print("invalid voltage please reenter correct voltage")
            return
        else:
            differential_voltage = voltage * 1/2
            volt_value_high=ul.from_eng_units(self.board_num, self.range, differential_voltage)
            volt_value_low=ul.from_eng_units(self.board_num, self.range, -1 * differential_voltage)
            ul.a_out(self.board_num, channel_high, self.range,volt_value_high)
            ul.a_out(self.board_num, channel_low, self.range,volt_value_low)
            return 


    def get_diff_voltage(self,channel_high,channel_low):
        '''
        Return differential voltage between 2 channels
        '''
        mode = self.mode
        if mode == "single_ended":
            diff_voltage = self.get_voltage(channel_high) - self.get_voltage(channel_low)
            return diff_voltage
        elif mode == "differential": 
            if channel_low == channel_high + 1 and channel_high % 2 == 0:
                return self.get_voltage(channel_high // 2)
            else:
                print("please use correct channels, refer to manual to connect to correct pin in differential mode")
                return "null"
        else:
            print("please use correct mode, single_ended or differential")
            return "null"
        
    def set_zero(self):
        '''
        Reset Galvo config
        '''
        for i in range(4):
            self.set_voltage(i,0)
        #ul.release_daq_device(self.board_num)
        return


    def get_counts(self, dt, counter_channel):
        """Implementing electrical pulse countings on the Daq cards
        Args:
            dt (float): time differential
            counter_channel (int): channel of the counter

        Returns:
            int: number of counts
        """
        # daq_dev_info = DaqDeviceInfo(self.board_num)
        # ctr_info = daq_dev_info.get_ctr_info()
        # if counter_channel != ctr_info.chan_info[counter_channel].channel_num:
        #     print("wrong channel")
        #     return "null"
        # else:
        ul.c_clear(self.board_num, counter_channel)
        t=0
        while t <= dt:
            t_start= time.perf_counter()
            counts = ul.c_in_32(self.board_num, counter_channel)
            t = (time.perf_counter() - t_start) + t
        return counts