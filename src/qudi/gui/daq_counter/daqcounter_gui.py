import os
import numpy as np

from qudi.core.module import GuiBase
from qudi.core.connector import Connector
from qtpy import QtWidgets
from qtpy import uic
from qudi.util.colordefs import QudiPalettePale as palette

class DAQCounterMainWindow(QtWidgets.QMainWindow):
    """ Create the Main Window based on the *.ui file. """

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'ui_daqcounter_gui.ui')

        # Load it
        super().__init__()
        uic.loadUi(ui_file, self)
        self.show()

class DAQCounterGUI(GuiBase):
    """
    DAQ Counter gui.
    """

    #Connector
    daq_counter_1 = Connector(interface='DaqCounter')
    daq_counter_2 = Connector(interface='DaqCounter')

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def on_activate(self):
        """ Activate the module
        """
        self._daq_counter_1 = self.daq_counter_1()
        self._daq_counter_2 = self.daq_counter_2()

        self._mw = DAQCounterMainWindow()

        self._daq_counter_1.sig_update_display.connect(self.count)
        self._daq_counter_1.sig_update_display.connect(self.count)

        self._daq_counter_1.sig_update_display.connect(self.update_plot)
        self._daq_counter_2.sig_update_display.connect(self.update_plot)

        self.time_pass = 0
        # Plot labels for 1st channel.
        self._pw = self._mw.countTrace1

        self.plot1 = self._pw.plotItem
        self.plot1.setLabel('left', 'Power Output', units='W', color='#00ff00')
        self.plot1.setLabel('bottom', 'Steps passed')

        self.curve_arr_1 = []
        ## Create an empty plot curve to be filled later, set its pen
        self.curve_arr_1.append(self.plot1.plot())
        self.curve_arr_1[-1].setPen(palette.c1)

        self.count_arr_1 = []

        # Plot labels for 2nd channel
        self._pw = self._mw.countTrace2

        self.plot2 = self._pw.plotItem
        self.plot2.setLabel('left', 'Power Output', units='W', color='#00ff00')
        self.plot2.setLabel('bottom', 'Steps passed')

        self.curve_arr_2 = []
        ## Create an empty plot curve to be filled later, set its pen
        self.curve_arr_2.append(self.plot2.plot())
        self.curve_arr_2[-1].setPen(palette.c2)

        self.count_arr_2 = []

        # Set default parameters
        self.count_1 = 0
        self.count_2 = 0

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()
        #return 0

    def count(self):
        self.count_1 = self._daq_counter_1.counts
        self.count_2 = self._daq_counter_2.counts
        self._mw.daq_channel1.setText(str(self.count_1))
        self._mw.daq_channel2.setText(str(self.count_2))


    def update_plot(self):
        """ The function that grabs the data and sends it to the plot.
        """
        self.time_pass += 1
        self.count_arr_1.append(self._daq_counter_1.counts)
        self.count_arr_2.append(self._daq_counter_2.counts)
        
        if (self.time_pass < 300):
            self.curve_arr_1[0].setData(
                y = np.asarray(self.count_arr_1),
                x = np.arange(0, self.time_pass)
                )
            self.curve_arr_2[0].setData(
                y = np.asarray(self.count_arr_2),
                x = np.arange(0, self.time_pass)
                )
        else:
            self.curve_arr_1[0].setData(
                y = np.asarray(self.count_arr_1[self.time_pass - 300:self.time_pass]),
                x = np.arange(self.time_pass - 300, self.time_pass)
                )
            self.curve_arr_2[0].setData(
                y = np.asarray(self.count_arr_2[self.time_pass - 300:self.time_pass]),
                x = np.arange(self.time_pass - 300, self.time_pass)
                )
            
    def show(self):
        self._mw.show()


