# Copyright 2023 Samuel Peana, Alina Stuleanu, Khoi Pham
#
# Implemented using thorlabs_apt_device package developed by Patrick C. Tapping
# 
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.


from thorlabs_apt_device import APTDevice
from thorlabs_apt_device.enums import EndPoint
import thorlabs_apt_device.protocol as apt
import serial.tools.list_ports
import threading
import time


class APTDevicePiezo(APTDevice):
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

    def __init__(self,serial_port=None, vid=None, pid=None, manufacturer=None, product=None, serial_number=None, 
                 location=None, controller=EndPoint.HOST, bays=(EndPoint.USB,), channels=(1,2), status_updates="polling"):

        super().__init__(serial_port=serial_port, vid=vid, pid=pid, manufacturer=manufacturer, product=product, serial_number=serial_number, 
                         location=location, controller=controller, bays=bays, channels=channels, status_updates=status_updates)

        self.message_event=threading.Event()

        #GET TPZ_IOSETTINGS to set max voltage for stage.
        self.keepalive_message=apt.pz_ack_pzstatusupdate
        self.update_message=apt.pz_req_pzstatusupdate
        for bay in self.bays:
            for channel in self.channels:
                self._loop.call_soon_threadsafe(self._write, apt.pz_req_tpz_iosettings(source=EndPoint.HOST, dest=bay, chan_ident=channel))

        self.info = []
        for channel in channels:
            # Max voltage for the NanoMax 303 Piezo Stage from ThorLabs is 75 V
            self.info.append({"channel": channel, "serial_number": serial_number, "voltage": 0, "max_voltage": 75, "mode": 2, "state": 1, 
                              "max_travel": 0, "position": 0})

            self.set_channel_state(channel=channel-1, state=1)
            self.set_zero(channel=channel-1)
            self.set_control_mode(channel=channel-1, mode=2)

        for channel in channels:
            max_travel = self.get_max_travel(channel=channel-1)
            self.info[channel-1]["max_travel"] = max_travel


    @classmethod
    def create(cls, serial_port=None, deviceID=None, vid=None, pid=None, manufacturer=None, product=None, serial_number=None, 
                 location=None, controller=EndPoint.HOST, bays=(EndPoint.USB,), channels=(1,2), status_updates="polling"):
        """ Create the APTDevicePiezo Class

        Args:
            serial_port (str, optional): serial port name. Defaults to None.
            deviceID (str, optional): device ID. Defaults to None.
            vid (_type_, optional): Dont change. Defaults to None.
            pid (_type_, optional): _description_. Defaults to None.
            manufacturer (_type_, optional): _description_. Defaults to None.
            product (_type_, optional): _description_. Defaults to None.
            serial_number (_type_, optional): _description_. Defaults to None.
            location (_type_, optional): _description_. Defaults to None.
            controller (_type_, optional): _description_. Defaults to EndPoint.HOST.
            bays (tuple, optional): _description_. Defaults to (EndPoint.USB,).
            channels (tuple, optional): _description_. Defaults to (1,2).
            status_updates (str, optional): _description_. Defaults to "polling".

        Returns:
            APTDevicePizeo: return the actual class object
        """
        if deviceID!=None:
            print("Attempting to connect")
            ports = list(serial.tools.list_ports.comports())
            for p in ports:
                serial_port="NODEVICE"
                if "APT" in p.description:
                    try:
                        serial_port = p.name
                        piezo=APTDevicePiezo(serial_port=serial_port, vid=vid, pid=pid, manufacturer=manufacturer, product=product, 
                                              serial_number=serial_number, location=location, controller=controller, bays=bays, channels=channels, 
                                              status_updates=status_updates)
                        if piezo.get_serial()==deviceID:
                            print("Connecting to Device " + deviceID + " on Port: " + serial_port)

                            for channel in channels:
                                piezo.info[channel-1]["serial_number"] = deviceID

                            break
                        else:
                            piezo.close()
                            while(piezo._port.is_open):
                                time.sleep(1)
                            serial_port="NODEVICE"
                    except:
                        print("Device on Port " + serial_port+" is not availabe!")   
            if serial_port=="NODEVICE":
                print("NO DEVICE WITH ID " + deviceID)
            else:
                return piezo           


    def get_channel_state(self, bay=0, channel=0, timeout=10):
        """
        Get the current channel state. 

        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        :param timeout: maximum delay for event to happpen
        """

        self._log.debug(f"Get Channel {channel} state on [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.mod_req_chanenablestate(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel]))

        self.message_event.wait(timeout=timeout)
        self.message_event.clear()

        return self.info[channel]["state"]


    def set_channel_state(self, bay=0, channel=0, state=1):
        """
        Set the channel state. 

        :param state: state of the piezo's state. (1: Enabled; 2: Disabled)
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """

        if (state != 1 and state != 2):
            raise ValueError("ENABLED : 1; DISABLED: 2")

        self._log.debug(f"Get Channel {channel} state on [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.mod_set_chanenablestate(source=EndPoint.HOST, dest=EndPoint.USB, chan_ident=self.channels[channel], enable_state=state))

        self.info[channel]["state"] = state


    def set_control_mode(self, bay=0, channel=0, mode=1):
        """
        Set the control Mode. 
        0x01 Open Loop (no feedback)
        0x02 Closed Loop (feedback employed)
        0x03 Open Loop Smooth
        0x04 Closed Loop Smooth

        :param mode: Mode of the piezo
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        if (mode < 0x01 or mode > 0x04):
            raise ValueError("CONTROL MODE MUST BE 0x01, 0x02, 0x03, or 0x04")

        self._log.debug(f"Set Channel {channel} mode to {mode} on [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.pz_set_positioncontrolmode(source=EndPoint.HOST, dest=EndPoint.USB, chan_ident=self.channels[channel], mode=mode))
        self.info[channel]["mode"] = mode


    def get_control_mode(self, bay=0, channel=0, timeout=10):
        """
        Get current control mode. 
        0x01 Open Loop (no feedback)
        0x02 Closed Loop (feedback employed)
        0x03 Open Loop Smooth
        0x04 Closed Loop Smooth

        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """

        self._log.debug(f"Get Channel {channel} state on [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.pz_req_positioncontrolmode(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel]))

        self.message_event.wait(timeout=timeout)
        self.message_event.clear()

        return self.info[channel]["mode"]


    def set_voltage(self, voltage=None, bay=0, channel=0):
        """
        Set the piezo voltage. Must be in Open Loop Mode, and must be manually set to this mode beforehand in the main or it will not work.

        :param voltage: Set current voltage as an integer in the range 
                        from 0 to 32767, correspond to 0-100% of piezo's max voltage.
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """

        curr_mode = self.info[channel]["mode"]

        if (curr_mode != 0x01 and curr_mode != 0x03):
            raise ValueError("MUST BE IN OPEN LOOP MODE")

        if (voltage == None):
            raise ValueError("PLEASE INPUT VOLTAGE")

        curr_max = self.info[channel]["max_voltage"]
        voltage_out=int(32767*(voltage/curr_max))

        self._log.debug(f"Sets output voltage {voltage} on [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.pz_set_outputvolts(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], voltage=voltage_out))

        self.info[channel]["voltage"] = voltage


    def get_voltage(self, bay=0, channel=0, timeout=10):
        """
        Get the piezo voltage.

        :param voltage: Get current voltage as an integer in the range 
                        from 0 to 32767, correspond to 0-100% of piezo's max voltage.
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """

        self._log.debug(f"Gets voltage on [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.pz_req_outputvolts(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel]))

        self.message_event.wait(timeout=timeout)
        self.message_event.clear()

        voltage = self.info[channel]["voltage"]
        max_voltage = self.info[channel]["max_voltage"]

        return voltage/32767*max_voltage


    def get_max_travel(self, bay=0, channel=0, timeout=10):
        """
        Get maximum travel distance.

        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        self._log.debug(f"Gets max_travel on [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.pz_req_maxtravel(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel]))

        self.message_event.wait(timeout=timeout)
        self.message_event.clear()

        return self.info[channel]["max_travel"]


    def set_position(self, position=None , bay=0, channel=0):
        """
        Set the position of the piezo.
        ONLY WORKS IN CLOSED LOOP MODE
        Units: microns

        :param position: Output position relative to zero position; sets as an integer in the range 
                         from 0 to 32767, correspond to 0-100% of piezo extension aka max_travel.
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        max = self.info[channel]["max_travel"]
        if (position == None):
            raise ValueError("MISSING INPUT FOR POSITION")

        if (position < 0):
            position_out = 0
            self.info[channel]["position"] = 0
            self._log.debug(f"Requested position not available. Sets position to 0 on [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
            self._loop.call_soon_threadsafe(self._write, apt.pz_set_outputpos(source=EndPoint.HOST, dest=self.bays[bay], 
                                                                              chan_ident=self.channels[channel], position=position_out))
            raise ValueError("POSITION MUST BE POSITIVE")

        curr_mode = self.info[channel]["mode"]

        if (curr_mode != 0x02 and curr_mode != 0x04):
            raise ValueError("MUST BE IN CLOSED LOOP MODE")

        position_out=int((32767.0*position/max))

        if (position_out > 32767):
            position_out = 32767
            self.info[channel]["position"] = max
            self._log.debug(f"Requested position not available. Sets position to max={max} on [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
            self._loop.call_soon_threadsafe(self._write, apt.pz_set_outputpos(source=EndPoint.HOST, dest=self.bays[bay], 
                                                                              chan_ident=self.channels[channel], position=position_out))
            raise ValueError("POSITION EXCEEDED MAX. SET POSITION TO MAX")


        self._log.debug(f"Sets position {position} on [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.pz_set_outputpos(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel], position=position_out))

        self.info[channel]["position"] = position


    def get_position(self , bay=0, channel=0, timeout=10):
        """
        Get position of the piezo as an integer in the range from 0 to 32767, correspond 
        to 0-100% of piezo extension aka max_travel.
        Units: microns

        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """

        curr_mode = self.info[channel]["mode"]

        if (curr_mode != 0x02 and curr_mode != 0x04):
            raise ValueError("MUST BE IN CLOSED LOOP MODE")

        self._log.debug(f"Sets position on [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.pz_req_outputpos(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel]))

        self.message_event.wait(timeout=timeout)
        self.message_event.clear()

        position = self.info[channel]["position"]
        max_travel = self.info[channel]["max_travel"]

        return position/32767*max_travel


    def set_zero(self , bay=0, channel=0):
        """
        Reads current position, and use that as reference for position 0.

        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        self._log.debug(f"Zero on [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        self._loop.call_soon_threadsafe(self._write, apt.pz_set_zero(source=EndPoint.HOST, dest=self.bays[bay], chan_ident=self.channels[channel]))


    def get_max_voltage(self , bay=0, channel=0):
        """
        Get max voltage.
        apt.pz_req_outputmaxvolts is not working, but the dictionary value for max_voltage can be accessed


        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """    
        # self._log.debug(f"Gets max output voltage on [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        # self._loop.call_soon_threadsafe(self._write, apt.pz_req_outputmaxvolts(source=EndPoint.USB, dest=self.bays[bay], chan_ident=self.channels[channel]))

        return self.info[channel]["max_voltage"] 


    def set_max_voltage(self, voltage=None , bay=0, channel=0):
        """
        Set max voltage.
        apt.pz_set_outputmaxvolts is not working, but the dictionary value for max_voltage can be overwritten by voltage

        :param voltage: Max voltage to set.
        :param bay: Index (0-based) of controller bay to send the command.
        :param channel: Index (0-based) of controller bay channel to send the command.
        """
        # self._log.debug(f"Sets max output voltage {voltage} on [bay={self.bays[bay]:#x}, channel={self.channels[channel]}].")
        # self._loop.call_soon_threadsafe(self._write, apt.pz_set_outputmaxvolts(source=EndPoint.USB, dest=self.bays[bay], chan_ident=self.channels[channel], voltage=voltage))

        self.info[channel]["max_voltage"] = voltage


    def get_serial(self, bay=0, timeout=10):
        """
        Get serial number.

        :param bay: Index (0-based) of controller bay to send the command.
        """    
        self._log.debug(f"Gets serial number [bay={self.bays[bay]:#x}.")
        self._loop.call_soon_threadsafe(self._write, apt.hw_req_info(source=EndPoint.HOST, dest=self.bays[bay]))

        self.message_event.wait(timeout=timeout)
        self.message_event.clear()

        return str(self.info[0]["serial_number"])


    def _process_message(self, m):
        super()._process_message(m)

        # Decode bay and channel IDs and check if they match one of ours
        if m.msg in ():
            if m.source == EndPoint.USB:
                # Map USB controller endpoint to first bay
                bay_i = 0
            else:
                # Check if source matches one of our bays
                try:
                    bay_i = self.bays.index(m.source)
                except ValueError:
                    # Ignore message from unknown bay id
                    if not m.source == 0:
                        # Some devices return zero as source of move_completed etc
                        self._log.warn(f"Message {m.msg} has unrecognised source={m.source}.")
                    bay_i = 0
            # Check if channel matches one of our channels
            try:
                channel_i = self.channels.index(m.chan_ident)
            except ValueError:
                    # Ignore message from unknown channel id
                    self._log.warn(f"Message {m.msg} has unrecognised channel={m.chan_ident}.")
                    channel_i = 0

        # Act on each message type
        if m.msg == "pz_get_outputvolts":
            self.info[m.chan_ident-1]["voltage"] = m.voltage
            self.message_event.set()

        elif m.msg == "pz_get_maxtravel":
            self.info[m.chan_ident-1]["max_travel"] = m.travel / 10
            self.message_event.set()

        elif m.msg == "pz_get_outputpos":
            self.info[m.chan_ident-1]["position"] = m.position
            self.message_event.set()

        elif m.msg=="mod_get_chanenablestate":
            self.info[m.chan_ident-1]["state"] = m.enabled
            self.message_event.set()

        elif m.msg=="pz_get_positioncontrolmode":
            self.info[m.chan_ident-1]["mode"] = m.mode
            self.message_event.set()

        elif m.msg=="hw_get_info":
            self.info[0]["serial_number"] = m.serial_number
            self.message_event.set()

        else:
            self._log.debug(f"Received message (unhandled): {m}")
            pass
