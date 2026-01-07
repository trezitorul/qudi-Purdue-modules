# -*- coding: utf-8 -*-
""" Logic module for the DAQ counter
"""

import time
from qudi.util.mutex import RecursiveMutex
from qudi.core.configoption import ConfigOption
from qudi.core.connector import Connector
from qudi.core.module import LogicBase
from qudi.util.datastorage import TextDataStorage
from qudi.core.statusvariable import StatusVar
import time
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline

# from logic.generic_logic import GenericLogic

from qtpy import QtCore


class polarization_measurement_logic(LogicBase):
    """ Logic module to interface with multichannel counting hardware.
    """
    counter_channels = ConfigOption(name='counter_channels', missing='error')#Dictionary with channel info and channel name.
    int_time = ConfigOption("IntegrationTime", 0.1)#Sets the default integration time per angle to 100ms
    counter = Connector(interface='counter_logic')
    pol_motor = Connector(interface='PolarMotorLogic')
    _poi_manager_logic = Connector(name='poi_manager_logic', interface='PoiManagerLogic')
    OPM = Connector(interface='OpmInterface')
    OPM = Connector(interface='OpmInterface')
    _optimizelogic = Connector(name='optimize_logic', interface='ScanningOptimizeLogic')
    _scan_logic = Connector(name='scanning_logic', interface='ScanningProbeLogic')
    #query_interval = ConfigOption('query_interval', 100) #How often to update the display
    #Global Variables
    initial_angle=0
    #Global Variables
    initial_angle=0
    data = [[],[]] #Nexted list, first list of elements are the scan angles used, and the second are the counter values at that angle.
    scan_angles =[] #Angles to be scanned on current scan
    stop_requested = False
    #Units
    stop_requested = False
    #Units
    S=1
    ms=1E-3*S
    #Variables
    _drift_correction_enabled = ConfigOption(name="drift_correction_enabled", missing="error")
    #Variables
    offset_table=StatusVar(name="offset_table", default=np.empty((0,3))) #Table of calibration offsets
    offset_splines=[]


    
    # signals
    sig_update_display = QtCore.Signal()
    sigSaveStateChanged = QtCore.Signal(bool)
    sigStartMeasurement = QtCore.Signal()
    sigStopMeasurement = QtCore.Signal()

    # signals for the save dialog to retrieve name and notes
    sigRequestSaveDialog = QtCore.Signal()
    sigSaveDialogExec = QtCore.Signal(str, str) # for filename, notes

    sigOptimizeStateUpdated = QtCore.Signal(bool) 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thread_lock = RecursiveMutex()
        self._filename = None
        self._notes = None
        self._optimization_running=False
        self._position_update=dict()


    def on_activate(self):
        """ Prepare logic module for work.
        """
        self._counter = self.counter()
        self.counter_channels = self._counter.get_counter_channels()
        self._poi = self._poi_manager_logic()
        self._OPM = self.OPM()

        self.stop_request = False
        self.buffer_length = 100
        self.set_exposure_time(self.int_time)
        
        self._pol_motor = self.pol_motor()

        #Signal Connect
        self.sigStartMeasurement.connect(self.start_measurement)
        self.sigStopMeasurement.connect(self.stop_measurement)

        # Connect callback for a finished refocus
        self._optimizelogic().sigOptimizeStateChanged.connect(
            self._optimisation_callback, QtCore.Qt.QueuedConnection)

        # delay timer for querying hardware
        #self.query_timer = QtCore.QTimer()
        #self.query_timer.setInterval(self.query_interval)
        #self.query_timer.setSingleShot(True)
        #self.query_timer.timeout.connect(self.check_loop, QtCore.Qt.QueuedConnection)

        # save dialog connections
        self.sigSaveDialogExec.connect(self._on_save_data_received) # does it make a difference if its here
        if len(self.offset_table)>0:
            self.offset_spline_calculator(self.offset_table)#Calculates the splines for the drift table to allow for smooth interpolation

        #QtCore.QTimer.singleShot(0, self.start_query_loop)

    def on_deactivate(self):
        """ When the module is deactivated
        """
        pass
        self._optimizelogic().sigOptimizeStateChanged.disconnect(self._optimisation_callback)
        #self.stop_query_loop()
        #for i in range(5):
            #time.sleep(self.query_interval / 1000)
            #QtCore.QCoreApplication.processEvents()
    
    @property
    def optimise_xy_size(self):
        return np.max([self._optimizelogic().scan_range['x'], self._optimizelogic().scan_range['y']])

    @QtCore.Slot()
    def initiate_measurement(self):
        print("INITIATE MEASUREMENT")
        self.sigStartMeasurement.emit()

    def start_measurement(self):
        print("START MEASUREMENT")
        self.stop_requested=False
        self._OPM.g2_mode()
        self.start_measurement_loop()

    @QtCore.Slot()
    def halt_measurement(self):
        self.stop_requested=True
        self.sigStopMeasurement.emit()

    @QtCore.Slot()
    def stop_measurement(self):
        # print("Stopping Measurement")
        self.stop_requested=True
        self._OPM.camera_mode()
        time.sleep(1)
        self._pol_motor.set_position(self.initial_angle)
        with self._thread_lock:
            if self.module_state() == 'locked':
                # print("Unlocking M")
                self.module_state.unlock()

    def set_scan_parameters(self, int_time, angles): 
        """Sets the parameters for a scan
            int_time: The integration time in seconds
            angles: A list of angles in degrees to be measured
        """
        self._counter.set_exposure_time(int_time*self.ms)
        self.scan_angles=angles

    #@QtCore.Slot()
    def start_measurement_loop(self):
        print('START MEASUREMENT LOOP')
        self.initial_angle = self._pol_motor.get_position()
        self.log.info("Starting Polarization Scan: " + str(self.scan_angles))
        """ Start the readout loop. """
        self.last_scan_start=datetime.now()
        self.data = []
        # self.query_timer.start(self.query_interval)
        self._counter.set_exposure_time(self.int_time)
        for angle in self.scan_angles:        
            if self.stop_requested:
                self.log.info("Polarization Measurement Stop Requested Halting Measurement")
                self.halt_measurement()
                self.sigMeasurementComplete.emit()
                break

            
            print("Setting Angle:" + str(angle))    
            self._pol_motor.set_position(angle)
            print("Angle Set")

            if self._drift_correction_enabled==True:
                offset = self.offset_calc(angle)
                print("Applying Offset: " + str(offset))
                curr_pos = self.scanner_position
                new_pos = [curr_pos[0] + offset[0], curr_pos[1] + offset[1], curr_pos[2]]
                
                if offset != [0,0]:
                    print("Moving Scanner to: " + str(new_pos))
                    self.move_scanner(position=new_pos)
                else:
                    print("Scanner at Optimal Position, No Move Applied")

            counts=self.get_counts()

            #counts = angle

            print("Measured Angle: " + str(angle) + "Measured Counts:" + str(counts))
            self.data.append([angle, counts])
            self.sig_update_display.emit()
        self.halt_measurement()
            #time.sleep(1)

    @QtCore.Slot(str, str)
    def _on_save_data_received(self, filename, notes):
        print("on save method triggered")
        self._filename = filename
        print("i got filename: ", filename)
        self._notes = notes
        print("i got notes: ", notes)

        # for persistent text:
        self._last_filename = filename
        self._last_notes = notes
        self._waiting.quit()

    def set_exposure_time(self,dt):
        self.int_time = dt
        self._counter.set_exposure_time(self.int_time)

    def get_exposure_time(self):
        self.dt=self._counter.get_exposure_time()
        return self.dt
    
    def get_counts(self):
        counts= self._counter.get_count_rates(self.counter_channels)
        counts = sum(counts)
        return counts
    
    def initiate_save(self):
        print("Initating Save")
        self.save(self.data)

    def plot_data(self, data, title=None):
        fig, ax = plt.subplots(subplot_kw={"projection":"polar"})
        theta = np.deg2rad(np.vstack(data)[0])
        r = np.vstack(data)[1]
        ax.plot([theta, r], label="Count Rate (cps)")
        ax.legend()
        if title is not None:        # Y-axis label
            ax.set_title(title)  # Title
        else:
            ax.set_title("Excitation Polarization Measurement")
        return fig

    def save(self, scan_data):
        print("Attempting to Save Excitation Polarization Data")
        with self._thread_lock:
            if self.module_state() != 'idle':
                self.log.error('Unable to save Excitation Polarization Measurment. Saving still in progress...')
                return

            if scan_data is None:
                raise ValueError('Unable to save Excitation Polarization Measurement. No data available.')

             # first you need to request the GUI to open the save dialog
            self.sigRequestSaveDialog.emit()
            print("i emitted to GUI")

            # listen for results?
            self._waiting = QtCore.QEventLoop()
            self._waiting.exec_()

            print("here is filename:", self._filename)
            print("here is notes:", self._notes)

            self.sigSaveStateChanged.emit(True)
            self.module_state.lock()
            try:
                ds = TextDataStorage(root_dir=self.module_default_data_dir)

                timestamp = datetime.now()
                # ToDo: Add meaningful metadata if missing:
                parameters = {}
                parameters["exposure_time"] = self.get_exposure_time()
                parameters['measurement start'] = self.last_scan_start
                parameters["r-axis name"] = "Counts"
                parameters["r-axis Units"] = "Counts"
                parameters["theta-axis name"] = "Angle"
                parameters["theta-axis units"] = "Degrees"

                print("im just before notes")
                # and then add another parameter item for the notes??
                parameters["notes"] = self._notes
                print("test")

                tag="Excitation Polarization Measurement_-" + self._filename

                print(self._poi_manager_logic().active_POI_Visible())
                if self._poi_manager_logic().active_POI_Visible():
                    parameters["ROI"]=self._poi_manager_logic().roi_name
                    parameters["POI"]=self._poi_manager_logic().active_poi
                    tag = "Excitation Polarization Scan of "+str(parameters["ROI"]+", "+str(parameters["POI"]))
                print(scan_data)
                file_path, _, _ = ds.save_data(scan_data,
                                                   metadata=parameters,
                                                   nametag=tag,
                                                   timestamp=timestamp,
                                                   column_headers='theta;;r')
                    # thumbnail
                figure = self.plot_data(scan_data, tag)
                ds.save_thumbnail(figure, file_path=file_path.rsplit('.', 1)[0])
            finally:
                self.log.info("Excitation Polarization Data Saved at: " + str(file_path))
                self.module_state.unlock()
                self.sigSaveStateChanged.emit(False)
            return

    @QtCore.Slot()
    def optimise_position(self, name=None, update_roi_position=True):
        """
        Triggers the optimisation procedure for the given poi using the optimizelogic.
        The difference between old and new position can be used to update the ROI position.
        This function will return immediately. The function "_optimisation_callback" will handle
        the aftermath of the optimisation.

        @param str name: Name of the POI for which to optimise the position.
        @param bool update_roi_position: Flag indicating if the ROI should be shifted accordingly.
        """
        with self._thread_lock:
            if self._optimizelogic().module_state() == 'idle':
                self._optimization_running = True
                self._optimizelogic().start_optimize()
                self.sigOptimizeStateUpdated.emit(True)
            else:
                self.log.warning('Unable to start refocus procedure. '
                                 'OptimizeLogic module is still locked.')
        return

    def _optimisation_callback(self, is_running, optimal_position=None, fit_data=None):
        """
        Callback function for a position optimisation.
        If desired the relative shift of the optimised POI can be used to update the ROI position.
        The scanner is moved to the optimised POI if desired.

        @param optimal_pos:
        @param fit_data:
        """
        with self._thread_lock:
            # If the refocus was initiated by poimanager, update POI and ROI position
            if self._optimization_running:
                if is_running:
                    self._position_update.update(optimal_position)
                else:
                    self._optimization_running = False
                    new_pos = np.array(list(self._position_update.values()))
                    self._optimizelogic().move_scanner(position=self._position_update)
                    self.sigOptimizeStateUpdated.emit(False)
        return
    
    def offset_calibration(self, cal_angles=None):
        offsets=[]
        if cal_angles is None:
            cal_angles = range(0, 360, 5)
        if 360 in cal_angles:
            cal_angles.remove(360)
        
        for angle in cal_angles:
            print("Setting Cal Angle:" + str(angle))    
            self._pol_motor.set_position(angle)
            print("Angle Set")

            if self._drift_correction_enabled==True:
                print("Optimize Initiated")
                self.log.debug("Optimizing Position for Polarization Angle: " + str(angle))
                self.optimise_position()
            

            while self._optimizelogic().module_state() != 'idle':
                print("Optimizing")
                time.sleep(1)
            self.log.debug("Position Optimized")
            offsets.append([angle, self._position_update["x"], self._position_update["y"]])
        self.offset_table.set_value(offsets)   
    

    def offset_spline_calculator(self, offsets):
        angles = offsets[0:-1, 0]
        offsets_x = offsets[0:-1, 1]
        offsets_y = offsets[0:-1, 2]
        angles=np.append(angles, angles[0] + 360)
        offsets_x=np.append(offsets_x, offsets_x[0])
        offsets_x=offsets_x-offsets_x[0]
        offsets_y=np.append(offsets_y, offsets_y[0])
        offsets_y=offsets_y-offsets_y[0]
        sx=CubicSpline(angles, offsets_x, bc_type="periodic")
        sy=CubicSpline(angles, offsets_y, bc_type="periodic")
        self.offset_splines=[sx, sy]

    def offset_calc(self, angle):
        if len(self.offset_table)>0:
            sx=self.offset_splines[0]
            sy=self.offset_splines[1]
            offset_x=sx(angle)
            offset_y=sy(angle)
        else:
            self.log.warn("Offset table empty, cannot apply drift correction, run offset calibration")
            return [0,0]
        return [offset_x, offset_y]
    
    def move_scanner(self, position):
        with self._thread_lock:
            if type(position) != dict:
                if len(position) != 3:
                    self.log.error('Scanner position to set must be dictionary or iterable of length 3.')
                    return
                position = {'x': position[0], 'y': position[1], 'z': position[2]}
            self._scan_logic().set_target_position(position)
            return
        
    @property
    def scanner_position(self):
        return np.array(list(self._scan_logic().scanner_position.values()))