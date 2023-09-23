# -*- coding: utf-8 -*-
""" Hardware module for APT Piezo

"""

from qudi.hardware.Piezo.APTDevice_Piezo import APTDevicePiezo
import time

from qudi.core.module import Base
from qudi.core.configoption import ConfigOption
from qudi.interface.confocal_devices_interface import ConfocalDevInterface


class APTPiezo(ConfocalDevInterface):
    """
    Initialise and open serial device for the ThorLabs APT controller.

    If the ``serial_port`` parameter is ``None`` (default), then an attempt to detect an APT device
    will be performed.
    The first device found will be initialised.
    If multiple devices are present on the system, then the use of the ``serial_number`` parameter
    will specify a particular device by its serial number.
    This is a `regular expression <https://docs.python.org/3/library/re.html>`_ match, for example
    ``serial_number="83"`` would match devices with serial numbers
    starting with 83, while ``serial_number=".*83$"`` would match devices ending in 83.

    Status updates can be obtained automatically from the device by setting ``status_updates="auto"``,
    which will request the controller to send regular updates, as well as sending the required "keepalive"
    acknowledgement messages to maintain the connection to the controller.
    In this case, ensure the :data:`keepalive_message` property is set correctly for the controller.

    To instead query the device for status updates on a regular basis, set ``status_updates="polled"``,
    in which case ensure the :data:`update_message` property is set correctly for the controller.

    The default setting of ``status_updates="none"`` will mean that no status updates will be
    performed, leaving the task up to sub-classes to implement.

    :param serial_port: Serial port device the device is connected to.
    :param vid: Numerical USB vendor ID to match.
    :param pid: Numerical USB product ID to match.
    :param manufacturer: Regular expression to match to a device manufacturer string.
    :param product: Regular expression to match to a device product string.
    :param serial_number: Regular expression to match to a device serial number.
    :param location: Regular expression to match to a device physical location (eg. USB port).
    :param controller: The destination :class:`EndPoint <thorlabs_apt_device.enums.EndPoint>` for the controller.
    :param bays: Tuple of :class:`EndPoint <thorlabs_apt_device.enums.EndPoint>`\\ (s) for the populated controller bays.
    :param channels: Tuple of indices (1-based) for the controller bay's channels.
    :param status_updates: Set to ``"auto"``, ``"polled"`` or ``"none"``.
    """
    deviceID = ConfigOption(name='deviceID', missing='warn')
    serial_port = ConfigOption(name='serial_port', missing='warn', default=None)
    is_second_piezo = ConfigOption(name='is_second_piezo', default=False)
    

    def on_activate(self):
        """ 
        Initialisation performed during activation of the module.
        """
        if (self.is_second_piezo):
            time.sleep(5)

        self.initialize()


    def on_deactivate(self):
        """
        Deinitialisation performed during deactivation of the module.
        """
        pass


    def initialize(self, channels=(1,2)):
        """ Initialization of the APTDevicePiezo class

        Args:
            channels channels: Channels of the Piezo. Defaults to (1,2).
        """
        
        if (self.serial_port == None):
            self.piezo = APTDevicePiezo.create(deviceID=self.deviceID, 
                                                channels=channels)
        else: 
            self.piezo = APTDevicePiezo(serial_port=self.serial_port, deviceID=self.deviceID, 
                                        channels=channels)
    

    def set_position(self, position=None , bay=0, channel=0):
        """
        Set the position of the piezo.
        ONLY WORKS IN CLOSED LOOP MODE
        Units: microns

        :param position: Output position relative to zero position; sets as an integer in the range 
                         from 0 to 32767, correspond to 0-100% of piezo extension aka maxTravel.
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        
        self.piezo.set_position(position=position, bay=bay, channel=channel)


    def get_position(self , bay=0, channel=0):
        """
        Get position of the piezo as an integer in the range from 0 to 32767, correspond 
        to 0-100% of piezo extension aka maxTravel.
        Units: microns

        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """

        return round(self.piezo.get_position(bay=bay, channel=channel), 2)
    
    def get_max_travel(self, channel=0):
        """ Get the maximum travel length of the piezo

        Args:
            channel (int, optional): _description_. Defaults to 0.

        Returns:
            int: max travel
        """

        return self.piezo.info[channel]["max_travel"]
