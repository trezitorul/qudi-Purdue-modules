# -*- coding: utf-8 -*-
# Hardware module the Ltune laser
# Copyright Alina Stuleanu 2023
# 
# RGB Lasersystems Lambda laser implementation, using the company's python integration example.

import serial
import time
import serial.tools.list_ports
from qudi.core.module import Base
from qudi.core.configoption import ConfigOption


class LtuneLaser(Base):
    deviceID = ConfigOption(name='deviceID', missing='warn', default=None)
    com_port = ConfigOption(name='com_port', missing='warn', default=None)
    """
    Open serial connection and initialize RGB Lasersystems Lambda device.

    :param com_port: com port device is connected to.
    :param deviceID: serial number of device.
    """
    def on_activate(self):
        """ Initialisation performed during activation of the module.
         """
        self.initialize(com_port=self.com_port, deviceID=self.deviceID)


    def on_deactivate(self):
        """
        Deinitialisation performed during deactivation of the module.
        """
        self.disable()
        self.close()


    def initialize(self, com_port=None, deviceID = None):
        """ Actually initialising the laser serial comm

        Args:
            com_port (str, optional): _description_. Defaults to None.
            deviceID (_type_, optional): _description_. Defaults to None.

        Raises:
            ValueError: _description_
            ValueError: _description_
        """
        if com_port == None:
            if len(deviceID)<5: 
                raise ValueError(f"Device {deviceID} is incorrect length")
            ports = list(serial.tools.list_ports.comports())
            for p in ports:
                serialNum = str(p.serial_number)
                serialNum = ''.join([char for char in serialNum if not char.isalpha()])
                if deviceID == serialNum:
                    com_port = p.name
                    print(f"Connecting to device {deviceID} on port {com_port}")
                    break
        if com_port == None:
            raise ValueError(f"Device {deviceID} could not be found.")

        # Start serial connection
        self.ser = serial.Serial(
                        port = com_port,
                        baudrate = 57600,
                        timeout = 10,            #in seconds
                        parity = serial.PARITY_NONE,
                        stopbits = serial.STOPBITS_ONE,
                        bytesize = serial.EIGHTBITS
                )
        
        self.com_port = com_port
        self.power = 0
        
        # Initialize laser at connection
        command = 'init\r\n'.encode()
        self.ser.write(bytes(command))


    def enable(self):
        """
        Enables laser. For safety reasons, the laser takes 5 seconds to turn on.
        """
        command = 'O=1\r\n'.encode()
        self.ser.write(bytes(command))
        self.enabled = True
        time.sleep(7)


    def disable(self):
        """
        Disables laser.
        """
        command = 'O=0\r\n'.encode()
        self.ser.write(bytes(command))
        self.enabled = False


    def close(self):
        """
        Closes serial connection.
        """
        self.ser.close()
    

    def set_output_power(self, power):
        """
        Sets output power to inputted value in mW.

        :param: power: power to set laser to in mW.
        """
        if not self.enabled:
            raise ValueError("Laser must be enabled to set output power!")

        command = f'P={power}\r\n'.encode()
        self.ser.write(bytes(command))
        self.power = power


    def get_output_power(self):
        """
        Returns output power in mW.
        """
        return self.power

