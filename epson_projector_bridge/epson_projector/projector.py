"""Main of Epson projector module."""
from .const import BUSY, TCP_PORT, HTTP_PORT, POWER, HTTP, TCP, SERIAL, EPSON_CONFIG_RANGES, EPSON_READOUTS
from .timeout import get_timeout

from .lock import Lock

import logging


_LOGGER = logging.getLogger(__name__)

console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s     - %(levelname)s - %(message)s")
)
_LOGGER.addHandler(console_handler)
_LOGGER.setLevel(logging.DEBUG)

# logging.basicConfig(level=logging.DEBUG)


class Projector:
    """
    Epson projector class.

    Control your projector with Python.
    """

    def __init__(
        self,
        host,
        websession=None,
        type=TCP,
        timeout_scale=1.0,
    ):
        """
        Epson Projector controller.

        :param str host:        Hostname/IP/serial to the projector
        :param obj websession:  Websession to pass for HTTP protocol
        :param timeout_scale    Factor to multiply default timeouts by (for slow projectors)

        """
        self._lock = Lock()
        self._type = type
        self._timeout_scale = timeout_scale
        self._power = None

        from .projector_tcp import ProjectorTcp

        self._host = host
        self._projector = ProjectorTcp(host, TCP_PORT)

    def close(self):
        """Close connection. Not used in HTTP"""
        self._projector.close()

    def set_timeout_scale(self, timeout_scale=1.0):
        self._timeout_scale = timeout_scale
    
    def translate_value_to_epson(self, value, value_translator_setting):
        if value_translator_setting == '21':
            return int(int(value) * 256/21)
        
        if value_translator_setting == '50-100':
            return int((int(value) - 50) / 5) * 25

        if value_translator_setting == '100':
            return int(int(value) * 256/101)

        return int(value)

    def translate_value_from_epson(self, value, value_translator_setting):
        if value_translator_setting == '50-100':
            return int(int(value) / 25 * 5 + 50)
        
        if value_translator_setting == '21':
            return round(int(value) * 21/256)
        
        if value_translator_setting == '100':
            return round(int(value) * 101/256)

        return value

    async def get_serial_number(self):
        return await self._projector.get_serial()

    async def get_power(self):
        """Get Power info."""
        _LOGGER.debug("Getting POWER info")
        power = await self.get_property(command=POWER)
        if power:
            self._power = power
        return self._power

    async def get_property(self, command, timeout=None):
        """Get property state from device."""
        _LOGGER.debug("Getting property %s", command)
        timeout = timeout if timeout else get_timeout(command, self._timeout_scale)
        if self._lock.checkLock():
            raise Exception("Cannot fetch value as connection is locked")

        return await self._projector.get_property(command=command, timeout=timeout)

    async def send_command(self, command):
        """Send command to Epson."""
        _LOGGER.debug("Sending command to projector %s", command)

        if self._lock.checkLock():
            raise Exception("Projector is busy!")

        self._lock.setLock(command)
        return await self._projector.send_command(
            command, get_timeout(command, self._timeout_scale)
        )

    async def read_config_value(self, config, timeout=None):
        """Read a config value from Epson."""
        if config in EPSON_CONFIG_RANGES:
            entry = EPSON_CONFIG_RANGES[config]
        elif config in EPSON_READOUTS:
            entry = EPSON_READOUTS[config]
        else:
            raise Exception(f"Error!!! Trying to read {config} is not accepted!")
        
        command = entry['epson_code']
        value_translator_setting = entry['value_translator']

        _LOGGER.debug("Getting property %s", command)

        timeout = timeout if timeout else get_timeout(command, self._timeout_scale)
        if self._lock.checkLock():
            raise Exception("Cannot fetch value as connection is locked")

        value = await self._projector.get_property(command=command, timeout=timeout)

        return self.translate_value_from_epson(value, value_translator_setting)
        

    async def send_config_value(self, config, value):
        """Send a config value to Epson."""
        if config not in EPSON_CONFIG_RANGES:
            raise Exception(f"Error!!! Trying to set {config} is not accepted!")
            
        base_comand = EPSON_CONFIG_RANGES[config]['epson_code']
        possible_range = EPSON_CONFIG_RANGES[config]['valid_range']
        value_translator_setting = EPSON_CONFIG_RANGES[config]['value_translator']

        value = self.translate_value_to_epson(value, value_translator_setting)

        if value not in possible_range:
            raise Exception(f"Error!!! Translated value {value} is not accepted in possible range for {config}!")
            
        command = f"{base_comand} {value}"

        _LOGGER.debug("Sending config value to projector %s", command)
        if self._lock.checkLock():
            raise Exception("Projector is busy!")

        # self._lock.setLock(command)
        return await self._projector.send_request(
            command=command, 
            timeout=get_timeout(command, self._timeout_scale)
        )

    async def send_request(self, command):
        if self._lock.checkLock():
            raise Exception("Projector is busy!")

        return await self._projector.send_request(params=command, timeout=10)
