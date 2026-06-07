#!/bin/sh
set -eu

PASSWORD_FILE="/mosquitto/config/passwords"
CONFIG_FILE="/mosquitto/config/mosquitto.conf"

if [ ! -f "/mosquitto/config/conf.d/production.conf" ]; then
    exec /docker-entrypoint.sh /usr/sbin/mosquitto -c "$CONFIG_FILE"
fi

# Strict validation check for production deployment
if [ -z "${MQTT_USERNAME:-}" ] || [ -z "${MQTT_PASSWORD:-}" ]; then
    echo "MQTT_USERNAME and MQTT_PASSWORD must be set in production" >&2
    exit 1
fi

touch "$PASSWORD_FILE"
chmod 0700 "$PASSWORD_FILE"

mosquitto_passwd -b "$PASSWORD_FILE" "$MQTT_USERNAME" "$MQTT_PASSWORD"

chown mosquitto:mosquitto "$PASSWORD_FILE"
chmod 0700 "$PASSWORD_FILE"

exec /docker-entrypoint.sh /usr/sbin/mosquitto -c "$CONFIG_FILE"
