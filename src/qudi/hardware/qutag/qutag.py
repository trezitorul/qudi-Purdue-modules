import sys
from typing import Any, Callable, Mapping, Optional
import numpy as np

sys.path.append("C:\\Users\\Ozymandias\\TCSPC_project\\QuTag\\quTAG_MC-Software_Python-examples-20220711 (1)\\quTAG_MC-Software_Python-examples-20220711")
sys.path.append("C:\\Users\\Ozymandias\\TCSPC_project\\LAC")
sys.path.append("C:\\Users\\Ozymandias\\TCSPC_project\\MFF101FlipperMirror")

try:
        import QuTAG_MC
except:
        Exception("Time Tagger wrapper QuTAG.py is not in the search path.")

from PyQt5.QtCore import QObject
from qtpy import QtCore
import time
from qudi.core.module import LogicBase

class Qutag(LogicBase):
    ns=1e-9
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_activate(self):
        self.qutag = QuTAG_MC.QuTAG()
    
    def on_deactivate(self):
        return super().on_deactivate()

    def get_counts(self, dt, counter_channel):
        return self.get_qutag_counts([counter_channel], dt)

    def get_qutag_counts(self, channels, exposureTime):
        #print(exposureTime)
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
    
    def configG2(self, histWidth, binCount, chan):
        self.qutag.enableHBT(True)
        self.qutag.setHBTInput(chan[0], chan[1])
        self.timeBase=self.qutag.getTimebase()
         
        binWidth=histWidth*self.ns/binCount #histWidth should be in nanoseconds
        self.qutag.setHBTParams(int(binWidth/self.timeBase), binCount)
        self.fct=self.qutag.createHBTFunction()
        

    def getG2(self):
        self.qutag.getHBTCorrelations(0, self.fct)
        self.qutag.calcHBTG2(self.fct)
        analyse=self.qutag.analyzeHBTFunction(self.fct)
        binCount=analyse[1]
        binWidth=analyse[2]*self.timeBase/self.ns
        print(self.qutag.getHBTParams())
        print(analyse)
        print(binCount)
        print(binWidth)
        return [np.linspace(-binCount*binWidth, binCount*binWidth, binCount), analyse[4]]
    
    def resetG2(self):
        self.qutag.resetHBTCorrelations()

    def getHBTIntegrationTime(self):
         return self.qutag.getHBTIntegrationTime()