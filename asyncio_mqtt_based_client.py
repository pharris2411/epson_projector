import asyncio
from contextlib import AsyncExitStack, asynccontextmanager
from random import randrange
from asyncio_mqtt import Client, MqttError
import json

import epson_projector as epson
from epson_projector.const import (
    EPSON_KEY_COMMANDS, 
    PWR_OFF_STATE,
    EPSON_CONFIG_RANGES
)

BASE_TOPIC = 'epson'
MQTT_HOST = '192.168.1.98'
EPSON_IP = '192.168.1.30'
EPSON_UNIQUE_IDENTIFIER = f'EPSON_AT_{EPSON_IP}'

async def epson_projector_bridge():
    async with AsyncExitStack() as stack:
        tasks = set()
        stack.push_async_callback(cancel_tasks, tasks)

        client = Client(MQTT_HOST)
        await stack.enter_async_context(client)

        projector = epson.Projector(host=EPSON_IP, type='tcp')

        await publish_homeassistant_discovery_config(projector, client)

        manager = client.filtered_messages(f"{BASE_TOPIC}/command/#")
        messages = await stack.enter_async_context(manager)
        task = asyncio.create_task(process_commands(messages, projector))
        tasks.add(task)

        # Subscribe to topic(s)
        # 🤔 Note that we subscribe *after* starting the message
        # loggers. Otherwise, we may miss retained messages.
        await client.subscribe(f"{BASE_TOPIC}/command/#")

        task =  asyncio.create_task(poll_projector_status(client, projector))

        tasks.add(task)

        # Wait for everything to complete (or fail due to, e.g., network
        # errors)
        await asyncio.gather(*tasks)

async def poll_projector_status(client, projector):
    while True:
        powerStatus = await projector.get_power()
        if powerStatus == PWR_OFF_STATE:
            await client.publish(f"{BASE_TOPIC}/state/power", "OFF")
        else:
            await client.publish(f"{BASE_TOPIC}/state/power", "ON")
            
            await get_all_config_values(client, projector)

        await asyncio.sleep(10)

async def get_all_config_values(client, projector):
    for key_name in EPSON_CONFIG_RANGES:
        value = await projector.read_config_value(key_name)

        await client.publish(f"{BASE_TOPIC}/state/{key_name}", int(value))

async def process_commands(messages, projector):
    async for message in messages:
        # 🤔 Note that we assume that the message paylod is an
        # UTF8-encoded string (hence the `bytes.decode` call).
        command = message.topic[len(f"{BASE_TOPIC}/command/"):]
        value = message.payload.decode()
        
        if command in EPSON_CONFIG_RANGES:
            await projector.send_config_value(command, value)
        elif command in EPSON_KEY_COMMANDS:
            await projector.send_command(command)
        elif command == "power":
            if value == 'OFF':
                await projector.send_command("PWR OFF")
            else:
                await projector.send_command("PWR ON")
        else:
            print(f"Unknown command {command}")

async def publish_homeassistant_discovery_config(projector, client):
    
    await client.publish(f"homeassistant/switch/{BASE_TOPIC}/power/config", 
        json.dumps({
            "name": "Epson Projector Power",
            "unique_id": f"{EPSON_UNIQUE_IDENTIFIER}_pwr",
            "command_topic": f"{BASE_TOPIC}/command/power", 
            "state_topic": f"{BASE_TOPIC}/state/power"
        })
    )

    for key_name, config in EPSON_CONFIG_RANGES.items():
        await client.publish(f"homeassistant/number/{BASE_TOPIC}/{key_name.lower()}/config", 
            json.dumps({
                "name": f"Epson Projector {config['human_name']}", 
                "unique_id": f"{EPSON_UNIQUE_IDENTIFIER}_{key_name.lower()}",
                "command_topic": f"{BASE_TOPIC}/command/{key_name}", 
                "state_topic": f"{BASE_TOPIC}/state/{key_name}",
                "min": min(config['humanized_range']),
                "max": max(config['humanized_range']),
                "step": (1,5)[config['value_translator'] == '50-100'],
                "unit_of_measurement": ('','%')[config['value_translator'] == '50-100'],
                "availability_topic": f"{BASE_TOPIC}/state/power",
                "payload_available": "ON",
                "payload_not_available": "OFF",
            })
        )
    
    for i in range(1,11):
        await client.publish(f"homeassistant/button/{BASE_TOPIC}/lens_memory_{i}/config", 
            json.dumps({
                "name": f"Epson Projector Load Lens Memory #{i}", 
                "unique_id": f"{EPSON_UNIQUE_IDENTIFIER}_lens_memory_{i}",
                "command_topic": f"{BASE_TOPIC}/command/LENS_MEMORY_{i}",
                "availability_topic": f"{BASE_TOPIC}/state/power",
                "payload_available": "ON",
                "payload_not_available": "OFF",
            })
        )

        await client.publish(f"homeassistant/button/{BASE_TOPIC}/image_memory_{i}/config", 
            json.dumps({
                "name": f"Epson Projector Load Image Memory #{i}", 
                "unique_id": f"{EPSON_UNIQUE_IDENTIFIER}_image_memory_{i}",
                "command_topic": f"{BASE_TOPIC}/command/MEMORY_{i}", 
                "availability_topic": f"{BASE_TOPIC}/state/power",
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
    reconnect_interval = 3  # [seconds]
    while True:
        try:
            await epson_projector_bridge()
        except MqttError as error:
            print(f'Error "{error}". Reconnecting in {reconnect_interval} seconds.')
        finally:
            await asyncio.sleep(reconnect_interval)


asyncio.run(main())