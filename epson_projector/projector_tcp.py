"""TCP connection of Epson projector module."""
import logging

import asyncio
import async_timeout

from .const import (
    BUSY,
    ESCVPNET_HELLO_COMMAND,
    ESCVPNETNAME,
    ERROR,
    CR,
    CR_COLON,
    GET_CR,
    EPSON_CODES,
    POWER,
    SERIAL_BYTE,
    TCP_SERIAL_PORT,
    EPSON_KEY_COMMANDS
)
from .timeout import get_timeout

_LOGGER = logging.getLogger(__name__)

console_handler = logging.StreamHandler()
console_handler.setFormatter(   
    logging.Formatter("%(asctime)s - [%(threadName)s] - %(name)s - %(levelname)s - %(message)s")
)
_LOGGER.addHandler(console_handler)
_LOGGER.setLevel(logging.DEBUG)

# logging.basicConfig(level=logging.DEBUG)


class ProjectorTcp:
    """
    Epson TCP connector
    """

    def __init__(self, host, port=3629):
        """
        Epson TCP connector

        :param str host:    IP address of Projector
        :param int port:    Port to connect to. Default 3629.
        """
        self._host = host
        self._port = port
        self._isOpen = False
        self._serial = None
        self._loop = asyncio.get_running_loop()

    async def async_init(self):
        """Async init to open connection with projector."""
        try:
            with async_timeout.timeout(10):
                self._reader, self._writer = await asyncio.open_connection(
                    host=self._host, port=self._port, loop=self._loop
                )
                self._writer.write(ESCVPNET_HELLO_COMMAND.encode())
                response = await self._reader.read(16)
                if response[0:10].decode() == ESCVPNETNAME and response[14] == 32:
                    self._isOpen = True
                    _LOGGER.info("Connection open")
                    return
                else:
                    _LOGGER.info("Cannot open connection to Epson")
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout error")
        except ConnectionRefusedError:
            _LOGGER.error("Connection refused Error")
        except OSError as err:
            _LOGGER.error("No route to host? %s", err)

    def close(self):
        if self._isOpen:
            self._writer.close()

    async def get_property(self, command, timeout, bytes_to_read=256):
        """Get property state from device."""
        response = await self.send_request(
            timeout=timeout, command=command + GET_CR, bytes_to_read=bytes_to_read
        )
        _LOGGER.debug(f"Response to command {command} is {response}")
        if not response:
            raise Exception("No response!")
        try:
            resp_beginning = f"{command}="
            index_of_response = response.find(resp_beginning)
            if index_of_response == -1:
                _LOGGER.debug(f"Response was not expected -- retrying a read")
                response = await self.read(bytes_to_read)
                _LOGGER.debug(f"Retried read resulted in command {command} is {response}")
                resp_beginning = f"{command}="
                index_of_response = response.find(resp_beginning)
                if index_of_response == -1:
                    raise Exception("No response!")
            return response[index_of_response:].replace(resp_beginning, "")
        except KeyError:
            raise Exception("Error fetching!")

    async def send_command(self, command, timeout):
        """Send command to Epson."""
        formatted_command = ' '.join( ' '.join(x) for x in EPSON_KEY_COMMANDS[command])

        _LOGGER.debug(f"Prepping command {formatted_command}")

        # if command == "PWR OFF":
        #     # need to send it twice...
        #     await self.send_request(timeout=timeout, command=formatted_command)

        response = await self.send_request(timeout=timeout, command=formatted_command)
        return response


    async def send_request(self, timeout, command, bytes_to_read=256):
        """Send TCP request to Epson."""
        formatted_command = command + CR

        if self._isOpen is False:
            await self.async_init()
        if self._isOpen and formatted_command:
            _LOGGER.debug(f"Sending command {formatted_command}")
            with async_timeout.timeout(timeout):
                self._writer.write(formatted_command.encode())
                return await self.read(bytes_to_read)
    
    async def read(self, bytes_to_read=256):
        response = await self._reader.read(bytes_to_read)
        _LOGGER.debug(f"Raw response: {response.decode()}")
        response = response.decode().replace(CR_COLON, "")
        if response == ERROR:
            raise Exception("No response!")
        return response

    async def get_serial(self):
        """Send TCP request for serial to Epson."""
        if not self._serial:
            try:
                with async_timeout.timeout(10):
                    power_on = await self.get_property(POWER, get_timeout(POWER))
                    if power_on == EPSON_CODES[POWER]:
                        reader, writer = await asyncio.open_connection(
                            host=self._host, port=TCP_SERIAL_PORT, loop=self._loop
                        )
                        _LOGGER.debug("Asking for serial number.")
                        writer.write(SERIAL_BYTE)
                        response = await reader.read(32)
                        self._serial = response[24:].decode()
                        writer.close()
                    else:
                        _LOGGER.error("Is projector turned on?")
            except asyncio.TimeoutError:
                _LOGGER.error(
                    "Timeout error receiving SERIAL of projector. Is projector turned on?"
                )
        return self._serial
