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

logging.getLogger("asyncio").setLevel(logging.DEBUG)

logging.getLogger("asyncio").setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - [%(threadName)s] - %(name)s - %(levelname)s - %(message)s")
)
_LOGGER.addHandler(console_handler)
_LOGGER.setLevel(logging.DEBUG)
# endregion Logging


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

        tasks.add(asyncio.create_task(poll_projector_properties(client, projector)))
        tasks.add(asyncio.create_task(poll_projector_status(client, projector)))

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

            if power_status == PWR_ON_STATE:
                # These aren't mutually exclusive, during initial startup may give weird codes which then breaks fetching
                # the rest of the config values -- only fetch them if we know it's on
                await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_power", "ON")
                await get_power_read_only(client, power_status)

        except Exception as inst:
            _LOGGER.warning(f"Exception thrown: {inst}")

        await asyncio.sleep(POWER_REFRESH_SECONDS)


async def poll_projector_properties(client, projector):
    while True:
        try:
            power_status = await projector.get_power()
            if power_status == PWR_ON_STATE:
                await get_all_config_values(client, projector)

        except Exception as inst:
            _LOGGER.warning(f"Exception thrown: {inst}")

        await asyncio.sleep(PROPERTIES_REFRESH_SECONDS)


async def get_all_config_values(client, projector):
    for key_name in EPSON_CONFIG_RANGES:
        try:
            value = await projector.read_config_value(key_name)

            await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_{key_name.lower()}", int(value))
        except Exception as inst:
            _LOGGER.warning(f"Exception thrown: {inst}")

    for key_name in EPSON_READOUTS:
        try:
            value = await projector.read_config_value(key_name)

            await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_{key_name.lower()}", int(value))
        except Exception as inst:
            _LOGGER.warning(f"Exception thrown: {inst}")

    await get_all_option_values(client, projector)


async def get_all_option_values(client, projector):
    for key_name, config in EPSON_OPTIONS.items():
        try:
            raw_value = await projector.get_property(config['epson_command'])
            for option in config['options']:
                if raw_value == option[2]:
                    await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_{key_name.lower()}", option[0])
                    break
        except Exception as inst:
            _LOGGER.warning(f"Exception thrown: {inst}")


async def get_single_option_value(client, projector, option_property):
    config = EPSON_OPTIONS[option_property]
    try:
        raw_value = None
        while True:
            try:
                raw_value = await projector.get_property(config['epson_command'])
                break
            except Exception as inst:
                _LOGGER.warning(f"Exception thrown: {inst}")
                await asyncio.sleep(1)
                continue

        if raw_value:
            for option in config['options']:
                if raw_value == option[2]:
                    await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_{option_property.lower()}", option[0])
    except Exception as inst:
        _LOGGER.warning(f"Exception thrown: {inst}")


async def get_power_read_only(client, power_status):
    config = EPSON_OPTIONS['POWER_READ_ONLY']
    try:
        for option in config['options']:
            if power_status == option[2]:
                await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_power_read_only", option[0])
                break
    except Exception as inst:
        _LOGGER.warning(f"Exception thrown: {inst}")


async def publish_message(client, topic, message):
    _LOGGER.debug(f"Publishing to MQTT: {topic} -- {message}\n")
    await client.publish(topic, message, retain=True)


async def process_commands(messages, projector, client):
    async for message in messages:
        # 🤔 Note that we assume that the message payload is an
        # UTF8-encoded string (hence the `bytes.decode` call).
        command = message.topic[len(f"{MQTT_BASE_TOPIC}/command/"):]
        _LOGGER.debug(f"raw command: {command}")
        command = str.upper(command.removeprefix(EPSON_NAME + "_"))
        value = message.payload.decode()

        _LOGGER.info(f"Execute command '{command}' with value of '{value}'")
        try:
            if command in EPSON_CONFIG_RANGES:
                await projector.send_config_value(command, value)

                new_value = await projector.read_config_value(command)
                await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_{command.lower()}", int(new_value))

            elif command in EPSON_KEY_COMMANDS:
                await projector.send_command(command)
            elif command in EPSON_OPTIONS:
                if EPSON_OPTIONS[command].get('read_only', False):
                    _LOGGER.debug(f"Command {command} is read-only, ignoring")
                else:
                    for option in EPSON_OPTIONS[command]['options']:
                        if value == option[0]:
                            await projector.send_command(option[1])
                            if EPSON_OPTIONS[command].get('epson_command', False):
                                await get_single_option_value(client, projector, command)
            elif command == f"POWER":
                current_power = await projector.get_power()
                # only turn ON power if it's OFF
                if value == "ON" and current_power == PWR_OFF_STATE:
                    await projector.send_command("PWR ON")
                    await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_power_read_only", "Warm Up")
                # only turn OFF power if it's ON
                elif value == "OFF" and current_power == PWR_ON_STATE:
                    await projector.send_command("PWR OFF")
                    await publish_message(client, f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_power_read_only", "Cool Down")
                else:
                    _LOGGER.error(f"Power command {command} with value {value} is not valid for current power state '{EPSON_POWER_STATES[current_power]}'.")

            else:
                _LOGGER.error(f"Unknown command {command}")
        except Exception as inst:
            _LOGGER.warning(f"---- Exception thrown: {inst}")


async def publish_homeassistant_discovery_config(projector, client):
    await publish_message(client, f"homeassistant/switch/{MQTT_BASE_TOPIC}/{EPSON_NAME}_power/config",
                          json.dumps({
                              "name": f"{EPSON_NAME} - Epson Projector Power",
                              "unique_id": f"{EPSON_NAME}_pwr",
                              "command_topic": f"{MQTT_BASE_TOPIC}/command/{EPSON_NAME}_power",
                              "state_topic": f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_power"
                          })
                          )

    for key_name, config in EPSON_CONFIG_RANGES.items():
        await publish_message(client,
                              f"homeassistant/number/{MQTT_BASE_TOPIC}/{EPSON_NAME}_{key_name.lower()}/config",
                              json.dumps({
                                  "name": f"{EPSON_NAME} - {config['human_name']}",
                                  "unique_id": f"{EPSON_NAME}_{key_name.lower()}",
                                  "command_topic": f"{MQTT_BASE_TOPIC}/command/{EPSON_NAME}_{key_name.lower()}",
                                  "state_topic": f"{MQTT_BASE_TOPIC}/state/{EPSON_NAME}_{key_name.lower()}",
                                  "min": min(config['humanized_range']),
                                  "max": max(config['humanized_range']),
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

    for i in range(1, 11):
        await publish_message(client,
                              f"homeassistant/button/{MQTT_BASE_TOPIC}/{EPSON_NAME}_lens_memory_{i}/config",
                              json.dumps({
                                  "name": f"{EPSON_NAME} - Load Lens Memory #{i}",
                                  "unique_id": f"{EPSON_NAME}_lens_memory_{i}",
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
                                  "state_topic": f"{MQTT_BASE_TOPIC}/state/{key_name.lower()}",
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