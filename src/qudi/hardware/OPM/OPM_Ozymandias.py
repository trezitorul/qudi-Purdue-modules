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
    spectrometer_flipper = Connector(name = 'spectrometer_flipper', interface='FlipperInterface')
    camera_flipper = Connector(name='camera_flipper', interface='FlipperInterface')
    shutter_flipper=Connector(name='shutterFlipper', interface="FlipperInterface")
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def on_activate(self):
        self._galvo = self.galvo()
        self._spectrometer_flipper=self.spectrometer_flipper()
        self._camera_flipper=self.camera_flipper()
        self._shutter_flipper=self.shutter_flipper()
        return False
    
    def shut_off(self):
        # open cam, lift cam mirr, spectro down and shuttle close
        try:
            self._shutter_flipper.SetMode("on")
            self._camera_flipper.SetMode('off')
            self._spectrometer_flipper.SetMode('on')
        except:
            self.log.error("Fail to shut off flippers")
    
    def camera_mode(self):
        # turn on cam mirror, set galvo 0, spectro down and shuttle open
        try:
            self._shutter_flipper.SetMode("on")
            self._spectrometer_flipper.SetMode('on')
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
            self._spectrometer_flipper.SetMode('off')
            self._shutter_flipper.SetMode("off")
            self.log.info("OPM Setting Mode to scanning Mode")
        except:
            self.log.error("OPM failed to setup for scanning")

    def spectrometer_mode(self):
        self._camera_flipper.SetMode("off")
        time.sleep(0.5)
        self._spectrometer_flipper.SetMode("on")
        self._shutter_flipper.SetMode("off")
        self.log.info("OPM Setting Mode to Spectrometer Mode")

    def g2_mode(self):
        try:
            self._camera_flipper.SetMode("off")
            time.sleep(0.5)
            self._spectrometer_flipper.SetMode("off")
            self._shutter_flipper.SetMode("off")
            self.log.info("OPM Setting Mode to G2 Mode")
        except:
            self.log.error("OPM failed to setup for G2")
            
    def on_deactivate(self):
        self._shutter_flipper.SetMode("on")
        self._spectrometer_flipper.SetMode("on")
        self._camera_flipper.SetMode("off")
        self.log.info("OPM Setting Mode to Idle")
