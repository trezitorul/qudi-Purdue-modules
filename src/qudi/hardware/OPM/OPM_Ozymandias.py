import numpy as np
import time

from qudi.core.configoption import ConfigOption
from qudi.core.connector import Connector
from qudi.interface.opm_interface import OpmInterface
from qtpy import QtCore

#This class configures the optical elements for various operation modes by moving the flippers and shutters into their appropriate locations.
#Currently the setup has the following configuration:
#Camera-Flipper is down (beamsplitter in front of camera) when the mode is set to "ON"
#Spectrometer Flipper is in the beam path when it is set to "off"
#Shutter is not yet programmed in

class OpmOzymandias(OpmInterface):
    galvo = Connector(name="galvo", interface='GalvoInterfuse')
    spectrometer_flipper = Connector(name = 'spectrometer_flipper', interface='FlipperMirror')
    camera_flipper = Connector(name='camera_flipper', interface='FlipperMirror')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def on_activate(self):
        self._galvo = self.galvo()
        self._spectrometer_flipper=self.spectrometer_flipper()
        self._camera_flipper=self.camera_flipper()
        pass
    
    def shut_off(self):
        # open cam, lift cam mirr, spectro down and shuttle close
        try:
            self._camera_flipper.SetMode('off')
            self._spectrometer_flipper.SetMode('off')
        except:
            self.log.error("Fail to shut off flippers")
    
    def camera_mode(self):
        # turn on cam mirror, set galvo 0, spectro down and shuttle open
        try:
            self._spectrometer_flipper.SetMode('off')
            time.sleep(0.5)
            self._camera_flipper.SetMode('on') 
            self.log.info("OPM Setting Mode to Camera Mode")
        except:
            self.log.error("OPM failed to setup for scanning")
    
    def scanning_mode(self):
        # turn on cam mirror, set galvo 0, spectro down and shuttle open
        try:
            self._galvo.set_position([0,0])
            self._camera_flipper.SetMode('off') #skeptical
            time.sleep(0.5)
            self._spectrometer_flipper.SetMode('on')
            self.log.info("OPM Setting Mode to scanning Mode")
        except:
            self.log.error("OPM failed to setup for scanning")

    def spectrometer_mode(self):
        self._camera_flipper.SetMode("off")
        time.sleep(0.5)
        self._spectrometer_flipper("off")
        self.log.info("OPM Setting Mode to Spectrometer Mode")

    def on_deactivate(self):
        self._spectrometer_flipper.SetMode("off")
        self._camera_flipper.SetMode("off")
        self.log.info("OPM Setting Mode to Idle")
