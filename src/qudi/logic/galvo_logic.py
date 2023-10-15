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

    galvo = Connector(name="galvoInterfuse", interface='GalvoInterfuse')
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
        self._galvo = self.galvo()
        self.m=1
        self.um=self.m*1e-6
        # self.um=1
        self.nm=(self.um/1000)
        self.stop_request = False
        
        # delay timer for querying hardware
        self.query_timer = QtCore.QTimer()
        self.query_timer.setInterval(self.query_interval)
        self.query_timer.setSingleShot(True)
        self.query_timer.timeout.connect(self.check_loop, QtCore.Qt.QueuedConnection)

        self._galvo.set_scale()
        self._galvo.set_position_range()
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
            self.position = self._galvo.get_position()
            self.diff_volt = [self._galvo.get_diff_voltage(0,1), self._galvo.get_diff_voltage(2,3)]
        except:
            qi = 3000
            self.log.exception("Exception in galvo status loop, throttling refresh rate.")

        self.query_timer.start(qi)
        self.sig_update_display.emit()


   