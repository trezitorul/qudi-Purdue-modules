import sys
from typing import Any, Callable, Mapping, Optional
import numpy as np
from qudi.interface.counter import Counter
from qudi.core.configoption import ConfigOption

sys.path.append("C:\\Users\\Ozymandias\\qudi-Purdue-modules\\src\\qudi\\hardware\\qutag")

try:
        import QuTAG_MC
        #from . import QuTAG_MC
except:
        Exception("Time Tagger wrapper QuTAG.py is not in the search path.")

from PyQt5.QtCore import QObject
from qtpy import QtCore
import time
#from qudi.core.module import LogicBase
from qudi.core.module import Base

class Qutag(Counter, Base):
    ns=1e-9
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_activate(self):
        self.qutag = QuTAG_MC.QuTAG()
    
    def on_deactivate(self):
        self.qutag.deInitialize()
        return 0
    
    def set_exposure_time(self, exposureTime):#exposure time is in ms
        self.qutag.setExposureTime(int(exposureTime*1000))

    def get_exposure_time(self):
        return self.qutag.getDeviceParams()[2]

    def get_counts(self, dt, counter_channel):
        return self.get_qutag_counts([counter_channel], dt)

    def get_qutag_counts(self, channels, exposureTime=None):
        #print(exposureTime)
        if exposureTime is not None:
            self.qutag.setExposureTime(int(exposureTime*1000))
        counts=0
        t=0
        #while t <= exposureTime:
        #    t_start= time.perf_counter()
        #    t = (time.perf_counter() - t_start) + t
        #time.sleep(exposureTime)
        updates=0
        while updates==0:
            data,updates = self.qutag.getCoincCounters()
        
        counts=[]
        for chan in channels:
            counts.append(data[chan])
        return counts
    
    def get_count_rates(self, channels):
        rates=self.get_qutag_counts(channels)
        exposureTime=self.get_exposure_time()/1000
        for i in range(len(rates)):
            rates[i]=rates[i]/exposureTime
        return rates
    
    def configG2(self, histWidth, binCount, g2_channels):
        self.g2_channels = g2_channels
        self.qutag.enableHBT(True)
        self.qutag.setHBTInput(g2_channels[0], g2_channels[1])
        self.timeBase=self.qutag.getTimebase()
         
        binWidth=histWidth*self.ns/binCount #histWidth should be in nanoseconds
        self.qutag.setHBTParams(int(binWidth/self.timeBase), binCount)
        self.fct=self.qutag.createHBTFunction()

    def configLifetime(self, histWidth, bincount, lifetime_channels, lifetime_delays):
        #histwidth in ns
        self.lifetime_channels = lifetime_channels
        self.lifetime_delays = lifetime_delays
        self.qutag.enableLFT(True)
        self.timeBase=self.qutag.getTimebase()
        binWidth = histWidth*self.ns/bincount
        self.lifetime_start_channel = self.lifetime_channels[0]
        self.lifetime_stop_channel = self.lifetime_channels[1]
        for i in range(len(self.lifetime_channels)-1):
            self.qutag.setChannelDelay(lifetime_channels[i+1], lifetime_delays[i])
        self.qutag.setLFTStartInput(self.lifetime_channels[0])
        self.qutag.setLFTParams(int(binWidth/self.timeBase), bincount)
        self.qutag.addLFTHistogram(self.lifetime_stop_channel,True)
        self.lft=self.qutag.createLFTFunction()

    def getLifetime(self):
        self.qutag.getLFTHistogram(self.lifetime_stop_channel,True,self.lft)
        analyse = self.qutag.analyseLFTFunction(self.lft)
        binCount = analyse[1]
        binWidth = analyse[2]*self.timeBase/self.ns
        return [np.linspace(0, binCount*binWidth, binCount), analyse[3]]
    
    def getLFTStartEvents(self):
        self.qutag.getLFTHistogram(self.lifetime_stop_channel,True,self.lft)
        histo = self.qutag.getLFTHistogram(self.lifetime_stop_channel, True, self.lft)
        return histo[2]
    
    def getLFTStopEvents(self):
        self.qutag.getLFTHistogram(self.lifetime_stop_channel,True,self.lft)
        histo = self.qutag.getLFTHistogram(self.lifetime_stop_channel, True, self.lft)
        return histo[3]
    
    def getLFTExposureTime(self):
        self.qutag.getLFTHistogram(self.lifetime_stop_channel,True,self.lft)
        histo = self.qutag.getLFTHistogram(self.lifetime_stop_channel, True, self.lft)
        return histo[4]
    
    def getLFTStats(self):
        self.qutag.getLFTHistogram(self.lifetime_stop_channel,True,self.lft)
        histo = self.qutag.getLFTHistogram(self.lifetime_stop_channel, True, self.lft)
        return histo[1:]

    def getG2(self):
        self.qutag.getHBTCorrelations(0, self.fct)
        self.qutag.calcHBTG2(self.fct)
        analyse=self.qutag.analyzeHBTFunction(self.fct)
        binCount=analyse[1]
        binWidth=analyse[2]*self.timeBase/self.ns
        return [np.linspace(-binCount*binWidth, binCount*binWidth, binCount), analyse[4]]
    
    def getHBTEventCount(self):
        return self.qutag.getHBTEventCount()
    
    def getHBTTotalCount(self):
        return self.getHBTEventCount()[0]
    
    def getHBTRate(self):
         return self.getHBTEventCount()[2]
    
    def getHBTCount(self):
         return self.getHBTEventCount()[1]
    
    def resetG2(self):
        self.qutag.resetHBTCorrelations()

    def resetLFT(self):
        self.qutag.resetLFTHistograms()

    def getHBTIntegrationTime(self):
         return self.qutag.getHBTIntegrationTime()
    
    def getHBTParameters(self):
        return self.qutag.getHBTParams()
    
    def getHBTBinWidth(self):
        return self.getHBTParameters()[0]
    
    def getHBTBinCount(self):
        return self.getHBTParameters()[1]

    def getLFTBinWidth(self):
        return self.qutag.getLFTParams[0]

    def getLFTBinCount(self):
        return self.qutag.getLFTParams[1]