import sys
from typing import Any, Callable, Mapping, Optional

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
        while t <= exposureTime:
            t_start= time.perf_counter()
            t = (time.perf_counter() - t_start) + t
        #time.sleep(exposureTime)
        data,updates = self.qutag.getCoincCounters()
        for chan in channels:
            counts+=data[chan]
        return counts
