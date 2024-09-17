# # -*- coding: utf-8 -*-

import numpy as np
# import time

# from PySide2 import QtCore
# from PySide2.QtGui import QGuiApplication

from qudi.interface.scanning_probe_interface import ScanningProbeInterface, ScanConstraints, \
     ScannerAxis, ScannerChannel, ScanData
from qudi.core.configoption import ConfigOption
from qudi.core.connector import Connector
from qudi.util.mutex import RecursiveMutex, Mutex
# from qudi.util.enums import SamplingOutputMode
# from qudi.util.helpers import in_range
from qudi.core.module import Base
import time

class OzymandiasScanningProbeInterfuse(ScanningProbeInterface):
    m=1
    um=1e-6*m
    
    _position_ranges = ConfigOption(name='position_ranges', missing='error') #Reads the position ranges of the tool, NOTICE THIS IS RELYING ON THE CALIBRATION TO BE DONE! TODO, figure out how to ensure calibration is done
    #I think that most of these things should actually 
    _frequency_ranges = ConfigOption(name='frequency_ranges', missing='error') ##Aka values written/retrieved per second; Check with connected HW for sensible constraints.Reads the maximum frequency ranges, in our case this is limited mostly by the speed at which python can communicate with the DAQ.
    _resolution_ranges = ConfigOption(name='resolution_ranges', missing='error') #The maximum and minimum resolution possible, in our case this would be 
    _input_channel_units = ConfigOption(name='input_channel_units', missing='error')#Stores the different channel inputs, the format is like a dict. ChannelName: Unit, for us that might be SPAD1: "c/s"
    
    stage = Connector(interface="MotorInterface")
    counter = Connector(interface='Qutag')
    OPM = Connector(interface='OpmInterface')

   
    _threaded = True  # Interfuse is by default not threaded.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_scan_frequency = -1 
        self._current_scan_ranges = [tuple(), tuple()]
        self._current_scan_axes = tuple()
        self._current_scan_resolution = tuple()


        self._constraints=None #Creates the constraints variable, this stores all of the limits of the tool. These constraints are used to check to make sure that the scan 
        #Scan requested does not go over the maximum ranges and capability of the tool.
        self._target_pos = dict()#Stores the current target position, this position normally will coincide with the actual current position after motion is completed
        self._stored_target_pos = dict()#Temp storage incase cursor is moving.
        self._old_pos = None # store previous position before calibrate, in case we want to set it back

        self._thread_lock_cursor = Mutex() #Locks the cursor while the scan is happening
        self._thread_lock_data = Mutex() #Locks the data while it updates from hardware
    
        self._scan_data = None #Temporary Container for the ScanData - Should be type ScanData and instantiated in configure_scan

    def on_activate(self):
        self._opm = self.OPM()
        
        #Instantiate the galvo and piezo hardware
        self._stage = self.stage()
        self._counter = self.counter()
        
        self._opm.camera_mode()
        
        #Set Constraints
        self._target_pos = self.get_position()  # get the initalize position
        axes = list()
        for axis in self._position_ranges:
            axes.append(ScannerAxis(name=axis,
                                    unit="m",
                                    value_range=self._position_ranges[axis],
                                    step_range=(0, abs(np.diff(self._position_ranges[axis]))),
                                    resolution_range=self._resolution_ranges[axis],
                                    frequency_range=self._frequency_ranges[axis]
                                    ))
            if self._target_pos[axis] not in self._position_ranges[axis]: # If out of range
                self._target_pos[axis] = (self._position_ranges[axis][0] + self._position_ranges[axis][-1]) / 2 # Set center
  
        channels=list()
        for channel, unit in self._input_channel_units.items():
            channels.append(ScannerChannel(name=channel,
                                           unit=unit,
                                           dtype=np.float64)) 

        self._constraints = ScanConstraints(axes=axes,
                                            channels=channels,
                                            backscan_configurable=False, #TODO, this has not been incorporated into the toolchain at the QUDI version level yet, will need to be updated
                                            has_position_feedback=False, #TODO this has not been incorporated into the tool chain at the QUDI version level yet, will need to be updated
                                            square_px_only=False #TODO this has not been incorporated into the tool chain at the QUDI version level yet, will need to be updated
                                            )

        self.move_absolute(self._target_pos)

    @property
    def is_scan_running(self):
        """
        Read-only flag indicating the module state.

        @return bool: scanning probe is running (True) or not (False)
        """
        # module state used to indicate hw timed scan running
        #self.log.debug(f"Module in state: {self.module_state()}")
        #assert self.module_state() in ('locked', 'idle')  # TODO what about other module states?
        if self.module_state() == 'locked':
            return True
        else:
            return False

    @property
    def scan_settings(self):

        settings = {'axes': tuple(self._current_scan_axes),
                    'range': tuple(self._current_scan_ranges),
                    'resolution': tuple(self._current_scan_resolution),
                    'frequency': self._current_scan_frequency}
        return settings

    def get_constraints(self):
        """ Get hardware constraints/limitations.

        @return dict: scanner constraints
        """
        return self._constraints

    def reset(self): #TODO
        """ Hard reset of the hardware.
        """
        pass

    def configure_scan(self, scan_settings):
        """ Configure the hardware with all parameters needed for a 1D or 2D scan.

        @param dict scan_settings: scan_settings dictionary holding all the parameters 'axes', 'resolution', 'ranges'
        #  TODO update docstring in interface

        @return (bool, ScanSettings): Failure indicator (fail=True),
                                      altered ScanSettings instance (same as "settings")
        """
        if self.is_scan_running:
            self.log.error('Unable to configure scan parameters while scan is running. '
                           'Stop scanning and try again.')
            return True, self.scan_settings

        print('Configure not scan running')
        axes = scan_settings.get('axes', self._current_scan_axes)
        ranges = tuple(
            (min(r), max(r)) for r in scan_settings.get('range', self._current_scan_ranges)
        )
        resolution = scan_settings.get('resolution', self._current_scan_resolution)
        frequency = float(scan_settings.get('frequency', self._current_scan_frequency))
        self.log.info("Scan Configured, range:" + str(ranges) + " resolution:" + str(resolution) + " frequency:" + str(frequency))
        if not set(axes).issubset(self._position_ranges):
            self.log.error('Unknown axes names encountered. Valid axes are: {0}'
                           ''.format(set(self._position_ranges)))
            return True, self.scan_settings

        if len(axes) != len(ranges) or len(axes) != len(resolution):
            self.log.error('"axes", "range" and "resolution" must have same length.')
            return True, self.scan_settings
        for i, ax in enumerate(axes):
            for axis_constr in self._constraints.axes.values():
                if ax == axis_constr.name:
                    break
            if ranges[i][0] < axis_constr.min_value or ranges[i][1] > axis_constr.max_value:
                self.log.error('Scan range out of bounds for axis "{0}". Maximum possible range'
                               ' is: {1}'.format(ax, axis_constr.value_range))
                return True, self.scan_settings
            if resolution[i] < axis_constr.min_resolution or resolution[i] > axis_constr.max_resolution:
                self.log.error('Scan resolution out of bounds for axis "{0}". Maximum possible '
                               'range is: {1}'.format(ax, axis_constr.resolution_range))
                return True, self.scan_settings
            if i == 0:
                if frequency < axis_constr.min_frequency or frequency > axis_constr.max_frequency:
                    self.log.error('Scan frequency out of bounds for fast axis "{0}". Maximum '
                                   'possible range is: {1}'
                                   ''.format(ax, axis_constr.frequency_range))
                    return True, self.scan_settings
        print("configure done sanity check")

        with self._thread_lock_data:
            try:
                self._scan_data = ScanData(
                    channels=tuple(self._constraints.channels.values()),
                    scan_axes=tuple(self._constraints.axes[ax] for ax in axes),
                    scan_range=ranges,
                    scan_resolution=tuple(resolution),
                    scan_frequency=frequency,
                    position_feedback_axes=None
                )
                
            except Exception as e:
                #print(e)
                self.log.exception("Scan Configuration Failed")
                self.log.exception(e)
                return True, self.scan_settings

        self._current_scan_resolution = tuple(resolution)
        self._current_scan_ranges = ranges
        self._current_scan_axes = tuple(axes)
        self._current_scan_frequency = frequency                    
        return False, self.scan_settings

    def move_absolute(self, position, velocity=None, blocking=False):
        """ Move the scanning probe to an absolute position as fast as possible or with a defined
        velocity.

        Log error and return current target position if something fails or a scan is in progress.

        @param bool blocking: If True this call returns only after the final position is reached.
               dict position: {axis:pos}
        """
        for axis, pos in position.items():
            self._target_pos[axis] = position[axis]

        # if self.is_scan_running:
        #     self.log.error('Cannot move the scanner while, scan is running')
        #     return self.get_target()

        if not set(position).issubset(self.get_constraints().axes):
            self.log.error('Invalid axes name in position')
            return self.get_target()
        
        try:
            self._stage.move_abs(self._target_pos,blocking)
            return self.get_target()
        except Exception as e:
            self.log.exception("Absolute Move Failed, Good Luck")
            self.log.exception(e)

    def move_relative(self, distance, velocity=None, blocking=False):
        """ Move the scanning probe by a relative distance from the current target position as fast
        as possible or with a defined velocity.

        Log error and return current target position if something fails or a 1D/2D scan is in
        progress.

        @param bool blocking: If True this call returns only after the final position is reached.

        """
        current_position = self.get_position()
        end_pos = {ax: current_position[ax] + distance[ax] for ax in distance}
        self.move_absolute(end_pos, velocity=velocity, blocking=blocking)

    def get_target(self):
        """ Get the current target position of the scanner hardware
        (i.e. the "theoretical" position).

        @return dict: current target position per axis.
        """
        if self.is_scan_running:
            return self._stored_target_pos
        else:
            return self._target_pos

    def get_position(self):
        """ Get a snapshot of the actual scanner position (i.e. from position feedback sensors).
        For the same target this value can fluctuate according to the scanners positioning accuracy.

        For scanning devices that do not have position feedback sensors, simply return the target
        position (see also: ScanningProbeInterface.get_target).

        @return dict: current position per axis.
        """
        with self._thread_lock_cursor:
            return self._stage.get_pos()

    def get_non_active_axis(self):
        for ax in ['x','y','z']:
            if ax not in self._current_scan_axes:
                return ax
        raise Exception("Cannot get nonactive axis")
    
    def start_scan(self):
        """

        @return (bool): Failure indicator (fail=True)
        """
        self.log.info("Starting Scan")
        lin_spaces={}
        self._opm.scanning_mode()
        with self._thread_lock_data:
            if self.module_state() != 'idle':
                self.log.error('Can not start scan. Scan already in progress.')
                return -1
            self._scan_data.new_scan()
            self._stored_target_pos = self.get_target().copy()
            self.module_state.lock()
            self._old_pos = self._stage.calibrate()
            i=0
            for axis in self._current_scan_axes:
                lin_spaces[axis]=np.linspace(self._current_scan_ranges[i][0],
                                   self._current_scan_ranges[i][1],
                                   self._current_scan_resolution[i])
                i+=1
            for ax in ["x", "y", "z"]:
                if ax not in lin_spaces.keys():
                    lin_spaces[ax]=np.array([self._target_pos[ax]])
            self.scanner_steps=lin_spaces
            self.line_to_scan=-1
        return True

    def stop_scan(self):
        """

        @return bool: Failure indicator (fail=True)
        """
        self.log.info("Stopping Scan")
        self._opm.camera_mode()
        with self._thread_lock_data:
            if self.module_state() == 'locked':
                self.module_state.unlock()
            if self._old_pos:
                self.move_absolute(self._old_pos)
            return False

    def scan_line(self, line_to_scan):
        # Find not active axes
        # Set not active axes position
        # Set the x, y, z list position
        line_path={}
        result={"APD1": [], "APD2":[], "SUM":[]}
        for ax in ["x", "y", "z"]:
            if len(self.scanner_steps[ax]==1):
                line_path[ax]=[self.scanner_steps[ax][0]]*self._current_scan_resolution[0]
        
        line_path[self._current_scan_axes[0]]=self.scanner_steps[self._current_scan_axes[0]]
        if len(self._current_scan_axes)==2:
            line_path[self._current_scan_axes[1]]=[self.scanner_steps[self._current_scan_axes[1]][line_to_scan]]*self._current_scan_resolution[0]
        
        #time.sleep(0.1)
        stepTimes=[]
        for k in range(self._current_scan_resolution[0]):
            if k==0:
                blocking=True #Blocks for each new line to avoid artifacts in the image.
            else:
                blocking=False
            start=time.perf_counter()
            self.move_absolute({"x":line_path["x"][k], "y":line_path["y"][k], "z":line_path["z"][k]}, blocking=blocking)
            #stop=time.perf_counter()
            #mvTime=stop-start
            counts=self._counter.get_qutag_counts([1,2], 1/self._current_scan_frequency)

            #ct1Stop=time.perf_counter()
            result["APD1"].append(counts[0])
            result["APD2"].append(counts[1])
            result["SUM"].append(counts[0]+counts[1])
            totalStop=time.perf_counter()
            stepTimes.append(totalStop-start)
            #print("Total Loop Step: " + str(totalStop-start))
        #print(stepTimes)
        result["APD1"]=np.array(result['APD1'])
        result["APD2"]=np.array(result['APD2'])
        result["SUM"]=np.array(result['SUM'])
        return result

    def get_scan_data(self):
        """

        @return (bool, ScanData): Failure indicator (fail=True), ScanData instance used in the scan
        """
        if self._scan_data is None:
            raise RuntimeError('ScanData is not yet configured, please call "configure_scan" first')
        try:
            with self._thread_lock_data:
                if self.module_state() != 'idle':
                    self.line_to_scan+=1
                    num_lines_to_scan=0
                    if self._scan_data.scan_dimension == 2: 
                        num_lines_to_scan=self._current_scan_resolution[1]-1   
                        for ch in self._constraints.channels:
                            self._scan_data.data[ch][:, self.line_to_scan] = self.scan_line(self.line_to_scan)[ch]
                    else: 
                        for ch in self._constraints.channels:
                            self._scan_data.data[ch] = self.scan_line(self.line_to_scan)[ch]
                        
                    if self.line_to_scan >= num_lines_to_scan:
                        self.log.info("Scan Complete")
                        self._opm.camera_mode()
                        self.module_state.unlock()
                return self._scan_data.copy()
        except Exception as e:
             self.log.exception(f"Exception in get_scan_data\n{e}")

    def emergency_stop(self):
        """

        @return:
        """
        pass
    
    def on_deactivate(self):
        pass
    