import numpy as np
import time

from qudi.core.configoption import ConfigOption
from qudi.core.connector import Connector
from qudi.core.module import LogicBase
from qtpy import QtCore

class OpmOzymandias(LogicBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def on_activate(self):
        #flipper1,2,galvo,
        self._spectrometer_flipper = Connector(interface='FlipperMirrorLogic')
        self._camera_flipper = Connector(interface='FlipperMirrorLogic')
        self._galvo = Connector(name="galvoInterfuse", interface='GalvoInterfuse')
    
    def shut_off(self):
        # open cam, lift cam mirr, spectro down and shuttle close
        try:
            self._camera_flipper.SetMode('on')
            self._spectrometer_flipper.SetMode('off')
        except:
            self.log.error("Fail to shut off flippers")
    
    def setup_scanning(self):
        # turn on cam mirror, set galvo 0, spectro down and shuttle open
        try:
            self._galvo.set_position([0,0])
            self._camera_flipper.SetMode('on') #skeptical
            self._spectrometer_flipper.SetMode('off')
        except:
            self.log.error("Fail to initiate scanning hardware")

    def spectrometer(self):
        pass