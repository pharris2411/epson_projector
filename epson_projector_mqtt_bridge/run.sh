#!/usr/bin/with-contenv bashio

MQTT_HOST=$(bashio::config 'mqtt_host')
MQTT_BASE_TOPIC=$(bashio::config 'mqtt_base_topic')
MQTT_USERNAME=$(bashio::config 'mqtt_username')
MQTT_PASSWORD=$(bashio::config 'mqtt_password')

EPSON_HOST=$(bashio::config 'epson_host')
EPSON_NAME=$(bashio::config 'epson_name')

LOGGING_LEVEL=$(bashio::config 'logging_level')

python /usr/src/app/asyncio_mqtt_based_client.py

CMD [ "/run.sh" ]