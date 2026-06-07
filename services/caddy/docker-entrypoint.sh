#!/bin/sh
set -eu

: "${GRAFANA_DOMAIN:?set GRAFANA_DOMAIN}"
: "${MQTT_DOMAIN:?set INGEST_DOMAIN}"

envsubst '${GRAFANA_DOMAIN} ${MQTT_DOMAIN}' \
	</etc/caddy/Caddyfile.template \
	>/etc/caddy/Caddyfile

exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
