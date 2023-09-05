# region Imports
import asyncio
from contextlib import AsyncExitStack, asynccontextmanager
from asyncio_mqtt import Client, MqttError
import json
import logging
import os

import epson_projector.projector as epson
from epson_projector.const import (
    EPSON_KEY_COMMANDS,
    EPSON_CONFIG_RANGES,
    EPSON_OPTIONS,
    EPSON_COMPLEX_FUNCTIONS,
    EPSON_READOUTS,
    EPSON_POWER_STATES,
    PWR_OFF_STATE,
    PWR_ON_STATE,
)
# endregion Imports

# region Environment Variables
MQTT_HOST = os.getenv('MQTT_HOST')
MQTT_USERNAME = os.getenv('MQTT_USERNAME', None)
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', None)
MQTT_BASE_TOPIC = os.getenv('MQTT_BASE_TOPIC', 'epson')
EPSON_HOST = os.getenv('EPSON_HOST')
EPSON_NAME = os.getenv('EPSON_NAME', EPSON_HOST)
RECONNECT_SECONDS = int(os.getenv('RECONNECT_SECONDS', 5))
POWER_REFRESH_SECONDS = int(os.getenv('POWER_REFRESH_SECONDS', 10))
PROPERTIES_REFRESH_SECONDS = int(os.getenv('PROPERTIES_REFRESH_SECONDS', 10))

if not MQTT_HOST or not EPSON_HOST:
    raise Exception('Missing environment config! Please make sure MQTT_HOST and EPSON_HOST environment variables are '
                    'set.')
# endregion Environment Variables

# region Logging
_LOGGER = logging.getLogger(__name__)

logging.getLogger("asyncio").setLevel(str.upper(os.getenv('LOGGING_LEVEL', 'INFO')))

console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - [%(threadName)s] - %(name)s - %(levelname)s - %(message)s")
)
_LOGGER.addHandler(console_handler)
_LOGGER.setLevel(str.upper(os.getenv('LOGGING_LEVEL', 'INFO')))
# endregion Logging

# variable to track power state for logging purposes ONLY
power_state = None

# tracking project busy-ness, including for multiple simultaneous commands
projector_busy = False


async def epson_projector_bridge():
    async with AsyncExitStack() as stack:
        tasks = set()
        stack.push_async_callback(cancel_tasks, tasks)

        client = Client(
            hostname=MQTT_HOST,
            username=MQTT_USERNAME,
            password=MQTT_PASSWORD
        )
        await stack.enter_async_context(client)

        projector = epson.Projector(host=EPSON_HOST, type='tcp')

        await publish_homeassistant_discovery_config(projector, client)

        manager = client.filtered_messages(f"{MQTT_BASE_TOPIC}/command/#")
        messages = await stack.enter_async_context(manager)
        task = asyncio.create_task(process_commands(messages, projector, client))
        tasks.add(task)

        # Subscribe to topic(s)
        # 🤔 Note that we subscribe *after* starting the message
        # loggers. Otherwise, we may miss retained messages.
        await client.subscribe(f"{MQTT_BASE_TOPIC}/command/#")

        tasks.add(asyncio.create_task(poll_projector_status(client, projector)))
        tasks.add(asyncio.create_task(poll_projector_properties(client, projector)))

        # Wait for everything to complete (or fail due to, e.g., network
        # errors)
        await asyncio.gather(*tasks)


async def poll_projector_status(client, projector):
    while True:
        try:
            power_status = await projector.get_power()
            if power_status == PWR_OFF_STATE:
                await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_power", "OFF")
                await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_power_read_only",
                                      "Standby, Network On")
                update_local_power_state_tracking("Standby")

            if power_status == PWR_ON_STATE:
                # These aren't mutually exclusive, during initial startup may give weird codes which then breaks fetching
                # the rest of the config values -- only fetch them if we know it's on
                await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_power", "ON")
                await get_power_read_only(client, power_status)
                update_local_power_state_tracking("On")

        except Exception as inst:
            _LOGGER.warning(f"4-Exception thrown: {inst}")

        await asyncio.sleep(POWER_REFRESH_SECONDS)


async def poll_projector_properties(client, projector):
    while True:
        try:
            power_status = await projector.get_power()
            if power_status == PWR_ON_STATE:
                await get_all_config_values(client, projector)
            await asyncio.sleep(PROPERTIES_REFRESH_SECONDS)

        except Exception as inst:
            _LOGGER.warning(f"5-Exception thrown: {inst}")
            await asyncio.sleep(RECONNECT_SECONDS)


async def get_all_config_values(client, projector):
    for key_name in EPSON_CONFIG_RANGES:
        try:
            value = await projector.read_config_value(key_name)
            await asyncio.sleep(0.01)

            await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_{key_name.lower()}", int(value))
        except Exception as inst:
            _LOGGER.debug(f"6-Exception thrown: {inst}")

    for key_name in EPSON_READOUTS:
        try:
            value = await projector.read_config_value(key_name)
            await asyncio.sleep(0.01)

            await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_{key_name.lower()}", int(value))
        except Exception as inst:
            _LOGGER.debug(f"7-Exception thrown: {inst}")

    await get_all_option_values(client, projector)


async def get_all_option_values(client, projector):
    for key_name in list(EPSON_OPTIONS.keys()) + list(EPSON_COMPLEX_FUNCTIONS.keys()):
        if key_name != "POWER_READ_ONLY":
            await get_single_option_value(client, projector, key_name, periodic_trigger=True)
            await asyncio.sleep(0.01)


async def get_single_option_value(client, projector, option_property, periodic_trigger=False, static_value=None):
    config = EPSON_OPTIONS.get(option_property, False) or EPSON_COMPLEX_FUNCTIONS[option_property]
    try:
        raw_value = None
        while True:
            try:
                # support disabling of periodic updates for complex options
                if (option_property in EPSON_COMPLEX_FUNCTIONS and
                        periodic_trigger and
                        config.get('no_periodic_update', False)
                ):
                    break

                # support the static setting of values without querying the projector.
                # useful for 'Send Command'
                if static_value:
                    raw_value = static_value
                else:
                    raw_value = await projector.get_property(config['epson_command'],
                                                             resp_beginning=config.get('response_starts_with', None))

                break
            except Exception as inst:
                _LOGGER.debug(f"1-Exception thrown: {inst}")
                await asyncio.sleep(1)
                continue

        if option_property in EPSON_OPTIONS and raw_value:
            for option in config['options']:
                if raw_value == option[2]:
                    await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_{option_property.lower()}", option[0])
                    return option[0]
        if option_property in EPSON_COMPLEX_FUNCTIONS and raw_value:
            if config.get('numbers_only', False):
                # remove all non-numeric or space characters from the raw_value
                processed_value = ''.join([x for x in raw_value if x.isdigit() or x == ' '])
                # split up the numbers by spaces, and discard any empty strings
                processed_value = [x for x in processed_value.split(' ') if x]
                # recombine the numbers into a list separated by spaces
                processed_value = ' '.join(processed_value)
                # output to the log
                _LOGGER.debug(f"Processed value: {processed_value}")
            else:
                processed_value = raw_value

            await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_{option_property.lower()}", processed_value)
            return processed_value

    except Exception as inst:
        _LOGGER.warning(f"2-Exception thrown: {inst}")


async def get_power_read_only(client, power_status):
    config = EPSON_OPTIONS['POWER_READ_ONLY']
    try:
        for option in config['options']:
            if power_status == option[2]:
                await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_power_read_only", option[0])
                break
    except Exception as inst:
        _LOGGER.warning(f"3-Exception thrown: {inst}")


async def publish_message(client, topic, message):
    _LOGGER.debug(f"Publishing to MQTT: {topic} -- {message}")
    await client.publish(topic, message, retain=True)


async def process_commands(messages, projector, client):
    async for message in messages:
        # 🤔 Note that we assume that the message payload is an
        # UTF8-encoded string (hence the `bytes.decode` call).
        command = message.topic[len(f"{MQTT_BASE_TOPIC}/command/"):]
        command = str.upper(command.removeprefix(EPSON_NAME + "_"))
        value = str.upper(message.payload.decode())
        global projector_busy

        while projector_busy:
            _LOGGER.debug(f"Projector is busy when trying to send command '{command}' -- will retry")
            await asyncio.sleep(.5)

        _LOGGER.info(f"Execute command '{command}' with value of '{value}'")
        try:
            # projector is busy
            if command != "POWER":
                projector_busy = True
                await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_busy", "ON")
                _LOGGER.debug("Projector is busy.")

            if command in EPSON_CONFIG_RANGES:
                _LOGGER.debug(f"{command} is a range.")

                # send configuration
                await projector.send_config_value(command, value)

                # read new configuration
                new_value = await projector.read_config_value(command)
                await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_{command.lower()}", int(new_value))

                _LOGGER.info(f"Projector reports that the new value for '{command}' is '{new_value}'")

            elif command in EPSON_KEY_COMMANDS:
                _LOGGER.debug(f"{command} is a key command.")
                await projector.send_command(command)

                # get a dummy value to delay the clearing of the busy flag
                await get_single_option_value(client, projector, "POWER_READ_ONLY")
            elif command in EPSON_OPTIONS:
                _LOGGER.debug(f"{command} is an option.")
                if EPSON_OPTIONS[command].get('read_only', False):
                    _LOGGER.debug(f"Command {command} is read-only and cannot be changed. Refreshing value from projector.")
                    await get_single_option_value(client, projector, command)
                else:
                    for option in EPSON_OPTIONS[command]['options']:
                        if value == option[0].upper():
                            _LOGGER.debug(f"Sending command option: {option[1]}")
                            await projector.send_command(option[1])
                            if EPSON_OPTIONS[command].get('epson_command', False):
                                _LOGGER.debug(f"Getting value for: {option[1]}")
                                new_value = await get_single_option_value(client, projector, command)
                                _LOGGER.info(f"Projector reports that the new value for '{command}' is '{new_value}'")
                                break
                            else:
                                _LOGGER.debug(f"Command {command} does not have an associated 'epson_command', ignoring.")
                                break
                    else:
                        _LOGGER.error(f"Option {value} is not valid for command {command}")
            elif command in EPSON_COMPLEX_FUNCTIONS:
                _LOGGER.debug(f"{command} is a complex option.")
                if EPSON_COMPLEX_FUNCTIONS[command].get('read_only', False):
                    _LOGGER.debug(f"Command {command} is read-only and cannot be changed. Refreshing value from projector.")
                    await get_single_option_value(client, projector, command)
                elif EPSON_COMPLEX_FUNCTIONS[command].get('triggers_properties_refresh', False):
                    _LOGGER.info(f"Command {command} triggers a refresh of all properties. Refreshing values from projector.")
                    await get_all_config_values(client, projector)
                    _LOGGER.info(f"Property refresh complete.")
                else:
                    epson_command_to_send = f"{EPSON_COMPLEX_FUNCTIONS[command]['epson_command']} {value}"
                    set_return_value = await projector.send_command(epson_command_to_send)
                    if EPSON_COMPLEX_FUNCTIONS[command].get('use_set_return_value', False):
                        _LOGGER.debug(f"Using get return value for: {epson_command_to_send}")
                        new_value = await get_single_option_value(client, projector, command, static_value=set_return_value)
                    else:
                        _LOGGER.debug(f"Getting value for: {epson_command_to_send}")
                        new_value = await get_single_option_value(client, projector, command)
                    _LOGGER.info(f"The new value for '{command}' is '{new_value}'")
            elif command == f"POWER":
                _LOGGER.debug(f"{command} is a power command.")
                current_power = await projector.get_power()
                # only turn ON power if it's OFF
                if value == "ON" and current_power == PWR_OFF_STATE:
                    await projector.send_command("PWR ON")
                    await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_power_read_only", "Warm Up")
                    update_local_power_state_tracking("Warm Up")

                # only turn OFF power if it's ON
                elif value == "OFF" and current_power == PWR_ON_STATE:
                    await projector.send_command("PWR OFF")
                    await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_power_read_only", "Cool Down")
                    update_local_power_state_tracking("Cool Down")
                else:
                    _LOGGER.error(f"Power command {command} with value {value} is not valid for current power state '{EPSON_POWER_STATES[current_power]}'.")

            else:
                _LOGGER.error(f"Unknown command {command}")
                return

        except Exception as inst:
            _LOGGER.warning(f"---- 8-Exception thrown: {inst}")

        # projector is no longer busy
        if command != "POWER":
            await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_busy", "OFF")
            projector_busy = False
            _LOGGER.debug("Projector is no longer busy.")


async def publish_homeassistant_discovery_config(projector, client):
    await publish_message(client, f"homeassistant/switch/{MQTT_BASE_TOPIC}/{EPSON_NAME}_power/config",
                          json.dumps({
                              "name": f"{EPSON_NAME} - Epson Projector Power",
                              "unique_id": f"{EPSON_NAME}_power",
                              "object_id": f"{EPSON_NAME}_power",
                              "command_topic": f"{MQTT_BASE_TOPIC}/command/{EPSON_NAME}_power",
                              "state_topic": f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_power"
                          })
                          )

    await publish_message(client, f"homeassistant/binary_sensor/{MQTT_BASE_TOPIC}/{EPSON_NAME}_busy/config",
                          json.dumps({
                                "name": f"{EPSON_NAME} - Projector Busy (Read Only)",
                                "unique_id": f"{EPSON_NAME}_busy",
                                "object_id": f"{EPSON_NAME}_busy",
                                "state_topic": f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_busy",
                          })
                          )

    for key_name, config in EPSON_CONFIG_RANGES.items():
        await publish_message(client,
                              f"homeassistant/number/{MQTT_BASE_TOPIC}/{EPSON_NAME}_{key_name.lower()}/config",
                              json.dumps({
                                  "name": f"{EPSON_NAME} - {config['human_name']}",
                                  "unique_id": f"{EPSON_NAME}_{key_name.lower()}",
                                  "object_id": f"{EPSON_NAME}_{key_name.lower()}",
                                  "command_topic": f"{MQTT_BASE_TOPIC}/command/{EPSON_NAME}_{key_name.lower()}",
                                  "state_topic": f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_{key_name.lower()}",
                                  "min": min(config['humanized_range']) if 'humanized_range' in config else None,
                                  "max": max(config['humanized_range']) if 'humanized_range' in config else None,
                                  "step": (1, 5)[config['value_translator'] == '50-100'],
                                  "unit_of_measurement": ('', '%')[config['value_translator'] == '50-100'],
                                  "availability_topic": f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_power",
                                  "payload_available": "ON",
                                  "payload_not_available": "OFF",
                              })
                              )

    for key_name, config in EPSON_OPTIONS.items():
        # special handling for the read-only POWER option
        if key_name == 'POWER_READ_ONLY':
            await publish_message(client,
                                  f"homeassistant/select/{MQTT_BASE_TOPIC}/{EPSON_NAME}_power_read_only/config",
                                  json.dumps({
                                      "name": f"{EPSON_NAME} - {config['human_name']}",
                                      "unique_id": f"{EPSON_NAME}_power_read_only",
                                      "object_id": f"{EPSON_NAME}_{key_name.lower()}",
                                      "command_topic": f"{MQTT_BASE_TOPIC}/command/{EPSON_NAME}_power_read_only",
                                      "state_topic": f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_power_read_only",
                                      "options": [
                                          x[0] for x in config['options']
                                      ],
                                  })
                                  )
        # everything else
        else:
            await publish_message(client,
                                  f"homeassistant/select/{MQTT_BASE_TOPIC}/{EPSON_NAME}_{key_name.lower()}/config",
                                  json.dumps({
                                      "name": f"{EPSON_NAME} - {config['human_name']}",
                                      "unique_id": f"{EPSON_NAME}_{key_name.lower()}",
                                      "object_id": f"{EPSON_NAME}_{key_name.lower()}",
                                      "command_topic": f"{MQTT_BASE_TOPIC}/command/{EPSON_NAME}_{key_name.lower()}",
                                      "state_topic": f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_{key_name.lower()}",
                                      "options": [
                                          x[0] for x in config['options']
                                      ],
                                      "availability_topic": f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_power",
                                      "payload_available": "ON",
                                      "payload_not_available": "OFF",
                                  })
                                  )

    for key_name, config in EPSON_COMPLEX_FUNCTIONS.items():
        entity_type = config.get('entity_type', 'text')
        await publish_message(client,
                              f"homeassistant/{entity_type}/{MQTT_BASE_TOPIC}/{EPSON_NAME}_{key_name.lower()}/config",
                              json.dumps({
                                  "name": f"{EPSON_NAME} - {config['human_name']}",
                                  "unique_id": f"{EPSON_NAME}_{key_name.lower()}",
                                  "object_id": f"{EPSON_NAME}_{key_name.lower()}",
                                  "command_topic": f"{MQTT_BASE_TOPIC}/command/{EPSON_NAME}_{key_name.lower()}",
                                  "state_topic": f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_{key_name.lower()}",
                                  "availability_topic": f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_power",
                                  "payload_available": "ON",
                                  "payload_not_available": "OFF",
                              })
                              )

    for i in range(1, 11):
        await publish_message(client,
                              f"homeassistant/button/{MQTT_BASE_TOPIC}/{EPSON_NAME}_lens_memory_{i}/config",
                              json.dumps({
                                  "name": f"{EPSON_NAME} - Load Lens Memory #{i}",
                                  "unique_id": f"{EPSON_NAME}_lens_memory_{i}",
                                  "object_id": f"{EPSON_NAME}_lens_memory_{i}",
                                  "command_topic": f"{MQTT_BASE_TOPIC}/command/{EPSON_NAME}_lens_memory_{i}",
                                  "availability_topic": f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_power",
                                  "payload_available": "ON",
                                  "payload_not_available": "OFF",
                              })
                              )

        await publish_message(client,
                              f"homeassistant/button/{MQTT_BASE_TOPIC}/{EPSON_NAME}_image_memory_{i}/config",
                              json.dumps({
                                  "name": f"{EPSON_NAME} - Load Image Memory #{i}",
                                  "unique_id": f"{EPSON_NAME}_image_memory_{i}",
                                  "object_id": f"{EPSON_NAME}_image_memory_{i}",
                                  "command_topic": f"{MQTT_BASE_TOPIC}/command/{EPSON_NAME}_memory_{i}",
                                  "availability_topic": f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_power",
                                  "payload_available": "ON",
                                  "payload_not_available": "OFF",
                              })
                              )

    for key_name, config in EPSON_READOUTS.items():
        await publish_message(client,
                              f"homeassistant/sensor/{MQTT_BASE_TOPIC}/{EPSON_NAME}_{key_name.lower()}/config",
                              json.dumps({
                                  "name": f"{EPSON_NAME} - {config['human_name']}",
                                  "unique_id": f"{EPSON_NAME}_{key_name.lower()}",
                                  "object_id": f"{EPSON_NAME}_{key_name.lower()}",
                                  "state_topic": f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_{key_name.lower()}",
                                  "availability_topic": f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_power",
                                  "payload_available": "ON",
                                  "payload_not_available": "OFF",
                              })
                              )


async def cancel_tasks(tasks):
    for task in tasks:
        if task.done():
            continue
        try:
            task.cancel()
            await task
        except asyncio.CancelledError:
            pass


def update_local_power_state_tracking(new_power_state):
    global power_state
    if new_power_state != power_state:
        power_state = new_power_state
        _LOGGER.info(f"Projector transitions to state: '{power_state}'")


async def main():
    # Run the epson_projector_bridge indefinitely. Reconnect automatically
    # if the connection is lost.
    while True:
        try:
            await epson_projector_bridge()
        except MqttError as error:
            _LOGGER.error(f'{error} | Reconnecting in {RECONNECT_SECONDS} seconds.')
        finally:
            await asyncio.sleep(RECONNECT_SECONDS)


asyncio.run(main(), debug=True)