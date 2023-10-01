# -*- coding: utf-8 -*-
""" Logic module for the DAQ counter
"""

import numpy as np
import time
import math

from qudi.core.configoption import ConfigOption
from qudi.core.connector import Connector
from qudi.core.module import LogicBase
from qtpy import QtCore
from qudi.util.mutex import RecursiveMutex


class GalvoLogic(LogicBase):
    """ Logic module for the galvo.
    """

    daq = Connector(interface='DAQ')
    query_interval = ConfigOption('query_interval', 100)

    position = [0,0]


    # Connect signals
    sig_update_display = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thread_lock = RecursiveMutex()

    def on_activate(self):
        """ Prepare logic module for work.
        """
        self._daq = self.daq()
        self.m=1
        self.um=self.m*1e-6
        # self.um=1
        self.nm=(self.um/1000)
        
        self.theta_high=0
        self.theta_low=1
        self.phi_high=2
        self.phi_low=3
        self.VToA=0.5 #Volts per Optical Scan Angle (1/2 * 1 V per Mechanical Angle, Optical Scan Angle is 2X Mechanical Scan Angle)
        self.Sx=10
        self.Sy=10
        self.projection_distance=(229)*self.um #1/tan(31) used for development only, corresponds to max displacement of the X axis at theta=31 degrees. Units can be chosen arbitrarily for now as um=1

        self.stop_request = False
        self.buffer_length = 100

        # delay timer for querying hardware
        self.query_timer = QtCore.QTimer()
        self.query_timer.setInterval(self.query_interval)
        self.query_timer.setSingleShot(True)
        self.query_timer.timeout.connect(self.check_loop, QtCore.Qt.QueuedConnection)

        self.set_scale()
        self.set_position_range()
        QtCore.QTimer.singleShot(0, self.start_query_loop)


    def on_deactivate(self):
        """ Deactivate modeule.
        """
        self.stop_query_loop()
        for i in range(5):
            time.sleep(self.query_interval / 1000)
            QtCore.QCoreApplication.processEvents()


    @QtCore.Slot()
    def start_query_loop(self):
        """ Start the readout loop. """
        if self.thread() is not QtCore.QThread.currentThread():
            QtCore.QMetaObject.invokeMethod(self,
                                            'start_query_loop',
                                            QtCore.Qt.BlockingQueuedConnection)
            return

        with self._thread_lock:
            if self.module_state() == 'idle':
                self.module_state.lock()
                self.query_timer.start(self.query_interval)

    @QtCore.Slot()
    def stop_query_loop(self):
        """ Stop the readout loop. """
        if self.thread() is not QtCore.QThread.currentThread():
            QtCore.QMetaObject.invokeMethod(self,
                                            'stop_query_loop',
                                            QtCore.Qt.BlockingQueuedConnection)
            return

        with self._thread_lock:
            if self.module_state() == 'locked':
                self.query_timer.stop()
                self.module_state.unlock()
    
    @QtCore.Slot()
    def check_loop(self):
        """ Get position and update display. """
        if self.stop_request:
            if self.module_state.can('stop'):
                self.module_state.stop()
            self.stop_request = False
            return
        qi = self.query_interval
        try:
            self.position = self.get_position()
            self.diff_volt = [self.get_diff_voltage(0,1), self.get_diff_voltage(2,3)]
        except:
            qi = 3000
            self.log.exception("Exception in galvo status loop, throttling refresh rate.")

        self.query_timer.start(qi)
        self.sig_update_display.emit()


    def set_scale(self):
        self.set_diff_voltage(self.theta_high, self.theta_low, 5)
        self.set_diff_voltage(self.phi_high, self.phi_low, 5)
        time.sleep(.1)
        measured_voltage_X = self.get_diff_voltage(self.theta_high, self.theta_low)
        measured_voltage_Y = self.get_diff_voltage(self.phi_high, self.phi_low)
        self.Sx = 5 / measured_voltage_X
        self.Sy = 5 / measured_voltage_Y
        # print("Galvo X Scale")
        # print(self.Sx)
        # print("Galvo Y Scale")
        # print(self.Sy)
        self.set_position([0,0])


    def set_position(self, position):
        """
        position in micrometers. does conversion in function
        """
        self.set_X(position[0]*self.Sx*self.um)
        self.set_Y(position[1]*self.Sy*self.um)
        # self.set_diff_voltage(0,1,position[0])
        # self.set_diff_voltage(2,3,position[1])


    def set_voltage_scaled(self, voltage):
        """Set the scaled voltage

        Args:
            voltage (_type_): Input voltage
        """
        galvo_position = [voltage[0]*self.Sx, voltage[1]*self.Sy]
        self.set_diff_voltage(0,1,galvo_position[0])
        self.set_diff_voltage(2,3,galvo_position[1])


    def move_galvo_pos(self, axis, direction, galvo_step_size):
        """ Move galvo based on position

        Args:
            axis (int): 012 corresponds to xyz
            direction (int): 1 corresponds to up/right; -1 corresponds to down/left
            galvo_step_size (float): Step size of the galvo
        """
        pos = self.get_position() # pos is in meters
        galvo_position = [pos[0]/self.um, pos[1]/self.um]

        galvo_position[axis] = galvo_position[axis] + galvo_step_size * direction
        self.set_position([galvo_position[0], galvo_position[1]])


    def move_galvo_volt(self, axis, direction, galvo_step_size):
        """ Move galvo based on voltage

        Args:
            axis (int): 012 corresponds to xyz
            direction (int): 1 corresponds to up/right; -1 corresponds to down/left
            galvo_step_size (float): Step size of the galvo
        """
        galvo_position = [self.get_diff_voltage(0,1), self.get_diff_voltage(2,3)]

        galvo_position[axis] = galvo_position[axis] + galvo_step_size * direction
        self.set_diff_voltage(0,1,galvo_position[0] * self.Sx)
        self.set_diff_voltage(2,3,galvo_position[1] * self.Sy)

    def get_position(self):
        """Get current position

        Returns:
            list: coordinates [x, y]
        """

        # position = [self.get_diff_voltage(0,1), self.get_diff_voltage(2,3)]
        position = [self.get_X(), self.get_Y()]
        
        return position
    
    def set_theta_angle(self, theta):
        """Set optical angle in respect to X axis

        Args:
            theta (floate): theta angle
        """ 
        V_theta=theta/(self.Sx*self.VToA)
        self.set_diff_voltage(self.theta_high,self.theta_low, V_theta)


    def set_phi_angle(self, phi):
        """Set optical angle in respect to Y axis

        Args:
            phi (float): phi angle
        """
        
        V_phi=phi/(self.Sy*self.VToA)
        self.set_diff_voltage(self.phi_high,self.phi_low, V_phi)


    def set_X(self, X):
        """Set horizontal positon of laser

        Args:
            X (floate): horizontal position
        """
        theta=math.degrees(np.arctan(X/self.projection_distance))
        self.set_theta_angle(theta)

    
    def set_Y(self, Y):
        """Set vertical position of laser

        Args:
            Y (float): vertical position
        """
        phi=math.degrees(np.arctan(Y/self.projection_distance))
        self.set_phi_angle(phi)

    
    def get_theta_angle(self):
        """Return optical angle in respect to X axis

        Returns:
            float: optical angle in respect to X axis
        """
        x_volt = self.get_diff_voltage(self.theta_high,self.theta_low)
        theta = x_volt * self.VToA*self.Sx
        return theta


    def get_X(self):
        """Return horizontal positon of laser

        Returns:
            float: horizontal position
        """
        theta = self.get_theta_angle()
        X_position = math.tan(math.radians(theta)) * self.projection_distance
        return X_position


    def get_phi_angle(self):
        """Return optical angle in respect to Y axis

        Returns:
            float: optical angle in respect to Y axis
        """
        Y_volt = self.get_diff_voltage(self.phi_high,self.phi_low)
        phi = Y_volt * self.VToA*self.Sy
        return phi


    def get_Y(self):
        """Return vertical position of laser

        Returns:
            float: vertical position
        """
        phi = self.get_phi_angle()
        Y_position = math.tan(math.radians(phi)) * self.projection_distance
        return Y_position


    def set_mode(self,mode):
        """Set the DAQ card to either "differential" or "single_ended"

        Args:
            mode (str): mode "differential" or "single_ended"
        """

        self._daq.set_mode(mode)


    def get_voltage(self,channel_in):
        """Return analog input channel's voltage

        Args:
            channel_in (int): input channel

        Returns:
            float: voltage
        """
        
        return self._daq.get_voltage(channel_in)


    def set_voltage(self,channel_out,voltage):
        """Set the analog output channel's voltage

        Args:
            channel_out (int): output channel
            voltage (float): voltage
        """
        self._daq.set_voltage(channel_out,voltage)


    def set_diff_voltage(self,channel_high, channel_low,voltage):
        """Set the analog output differential voltage between 2 channel

        Args:
            channel_high (int): channel hight
            channel_low (int): channel low
            voltage (float): voltage
        """ 
        self._daq.set_diff_voltage(channel_high, channel_low,voltage)


    def get_diff_voltage(self,channel_high,channel_low):
        """Return differential voltage between 2 channels

        Args:
            channel_high (int): high voltage channel
            channel_low (int): low voltage channel

        Returns:
            float: diff voltage
        """
        return self._daq.get_diff_voltage(channel_high,channel_low)


    def set_position_range(self): 
        """set the position of the range
        """
        self.set_diff_voltage(self.theta_high, self.theta_low, 20)
        self.set_diff_voltage(self.phi_high, self.phi_low, 20)
        time.sleep(.1)
        measured_max_voltage_X = self.get_diff_voltage(self.theta_high, self.theta_low)
        measured_max_voltage_Y = self.get_diff_voltage(self.phi_high, self.phi_low)
        phi = measured_max_voltage_X / (self.VToA)
        max_Y=math.tan(math.radians(phi)) * self.projection_distance
        theta = measured_max_voltage_Y / (self.VToA)
        max_X=math.tan(math.radians(theta)) * self.projection_distance
        # print("GALVO MAX TRAVEL")
        # print([[-max_X, max_X], [-max_Y,max_Y]])
        self.pos_range = [[-max_X, max_X], [-max_Y,max_Y]]

    def get_position_range(self): 
        """get the position range

        Returns:
            nested list: maximum range in X and Y
        """

        return self.pos_range