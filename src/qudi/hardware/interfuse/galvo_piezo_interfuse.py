from typing import Any, Callable, Mapping, Optional
from qudi.interface.motor_interface import MotorInterface
from qudi.core.configoption import ConfigOption
from qudi.core.connector import Connector

class GalvoPiezoInterfuse(MotorInterface):
    m=1
    um=1e-6*m

    galvo = Connector(interface="GalvoInterfuse")
    piezo = Connector(interface='ConfocalDevInterface')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def on_activate(self):
        self._galvo = self.galvo()
        self._piezo = self.piezo()

        return 0
    
    def on_deactivate(self):
        pass

    def get_constraints(self):
        pass

    def move_abs(self, param_dict):
            self._galvo.set_position((param_dict['x']/self.um, param_dict["y"]/self.um))
            self._piezo.set_position(position=param_dict["z"]/self.um)

    def move_rel(self, param_dict):
        current_position = self.get_pos()
        end_pos = {ax: current_position[ax] + param_dict[ax] for ax in param_dict}
        self.move_abs(end_pos)

    def get_pos(self):
            positions_data = dict()
            xy = self._galvo.get_position()
            z = self._piezo.get_position()
            positions_data['x'] = xy[0]
            positions_data['y'] = xy[1]
            positions_data['z'] = z*self.um
            return positions_data

    def abort(self):
        pass

    def set_velocity(self, param_dict):
        pass
    
    def get_velocity(self, param_list=None):
        pass

    def get_status(self, param_list=None):
        pass

    def calibrate(self, param_list=None):
        pass
