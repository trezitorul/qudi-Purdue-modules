from typing import Any, Callable, Mapping, Optional
from qudi.interface.motor_interface import MotorInterface
from qudi.core.configoption import ConfigOption
from qudi.core.connector import Connector
from pipython import GCSDevice, GCSError, gcserror,pitools


class PI_Piezo_Stage(MotorInterface):
    m=1
    um=1e-6*m
    
    _controller_type=ConfigOption(name="piezo_controller_type", missing="error")
    _serial_num = ConfigOption(name='serial_number', missing='error')
    _axis_mapping = ConfigOption(name = "axis_mapping", missing='error')
    
   # _reverse_axis_mapping={_axis_mapping[key]: key for key in _axis_mapping}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._reverse_axis_mapping={self._axis_mapping[key]: key for key in self._axis_mapping}
    
    def on_activate(self):
        self._piezo=GCSDevice(self._controller_type)
        self._piezo.ConnectUSB(serialnum=self._serial_num)
        self.log.info(self._piezo.qIDN() + " Connected Successfully")
        return 0
    
    def on_deactivate(self):
        try:
            self._piezo.CloseConnection()
            self.log.info(self._piezo.qIDN()+" Disconnected Successfully")
        except:
            self.log.warn(self._piezo.qIDN()+" Did not Deactivate Successfully")

    def get_constraints(self):
        self.log.warn("Constraints not implemented yet")
    
    def move_abs(self, param_dict, blocking=False):
        try:
            self._piezo.MOV({self._axis_mapping[ax]:param_dict[ax]/self.um for ax in param_dict})
            if blocking:
                pitools.waitontarget(self._piezo, [self._axis_mapping[ax] for ax in param_dict])
        except GCSError as exc:
            self.log.error(exc)

    def move_rel(self, param_dict):
        current_position = self._piezo.qPOS()
        current_position = {self._reverse_axis_mapping[ax]: current_position[ax]/self.um for ax in current_position}
        end_pos = {ax: current_position[ax] + param_dict[ax]/self.um for ax in param_dict}
        end_pos = {self._axis_mapping[ax]:end_pos[ax] for ax in end_pos}
        self.move_abs(end_pos)

    def get_pos(self):
        current_position = self._piezo.qPOS()
        current_position = {self._reverse_axis_mapping[ax]: current_position[ax]*self.um for ax in current_position}
        return current_position

    def abort(self):
        pass

    def set_velocity(self, param_dict):
        pass
    
    def get_velocity(self, param_list=None):
        pass

    def get_status(self, param_list=None):
        pass

    def calibrate(self, param_list=None):
        old_pos =  self.get_pos
        self.move_abs({'x':0, 'y':0, 'z':0})
        return old_pos