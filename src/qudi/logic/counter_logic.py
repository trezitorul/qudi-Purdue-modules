# -*- coding: utf-8 -*-
""" Logic module for the DAQ counter
"""

import time
from qudi.util.mutex import RecursiveMutex
from qudi.core.configoption import ConfigOption
from qudi.core.connector import Connector
from qudi.core.module import LogicBase

# from logic.generic_logic import GenericLogic

from qtpy import QtCore


class counter_logic(LogicBase):
    """ Logic module to interface with multichannel counting hardware.
    """
    counter_channels = ConfigOption(name='counter_channels', missing='error')#Dictionary with channel info and channel name.
    dt = ConfigOption('dt', .001) 
    counter = Connector(interface='Counter')
    query_interval = ConfigOption('query_interval', 100)
    counts = 0

    
    # signals
    sig_update_display = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thread_lock = RecursiveMutex()

    def on_activate(self):
        """ Prepare logic module for work.
        """
        self._counter = self.counter()

        self.stop_request = False
        self.buffer_length = 100
        self.set_exposure_time(self.dt)

        # delay timer for querying hardware
        self.query_timer = QtCore.QTimer()
        self.query_timer.setInterval(self.query_interval)
        self.query_timer.setSingleShot(True)
        self.query_timer.timeout.connect(self.check_loop, QtCore.Qt.QueuedConnection)

        QtCore.QTimer.singleShot(0, self.start_query_loop)

    def on_deactivate(self):
        """ When the module is deactivated
        """
        self.stop_query_loop()
        for i in range(5):
            time.sleep(self.query_interval / 1000)
            QtCore.QCoreApplication.processEvents()

    @QtCore.Slot()
    def start_query_loop(self):
        """ Start the readout loop. """
        # self.query_timer.start(self.query_interval)

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
        """ Get counts and update display. """
        if self.stop_request:
            if self.module_state.can('stop'):
                self.module_state.stop()
            self.stop_request = False
            return
        qi = self.query_interval
        try:
            self.counts = self.get_counts(self.get_counter_channels().values())

        except:
            qi = 3000
            self.log.exception("Exception in counter status loop, throttling refresh rate.")

        self.query_timer.start(qi)
        self.sig_update_display.emit()

    def set_exposure_time(self,dt):
        self.dt = dt
        self._counter.set_exposure_time(dt)

    def get_exposure_time(self):
        #self.dt=self._counter.get_exposure_time()
        return self._counter.get_exposure_time()
    
    def get_channel_names(self):
        return self.counter_channels.keys()

    def get_channel_address(self, name):
        try:
            return self.counter_channels[name]
        except Exception as e:
            self.log.error(e)

    def channel_input_converter(self, channels):
        channel_address = []
        for channel in channels:
            if channel in self.counter_channels.values():
                channel_address.append(channel)
            elif channel in self.counter_channels.keys():
                channel_address.append(self.get_channel_address(channel))
            else:
                self.log.error(str(channel) + " Is not a valid counter channel name or address")
                return []
        return channel_address

    def get_counts(self, channels):
        self._counter.get_counts(self.dt, self.channel_input_converter(channels))

    def get_count_rates(self, channels):
        '''
        Implementing electrical pulse countings on the Daq cards
        Args:
            dt (floats): time differential
        Return number of counts
        '''
        return self._counter.get_count_rates(self.channel_input_converter(channels))
    
    def get_counter_channels(self):
        return self.counter_channels