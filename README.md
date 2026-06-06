# Acoupi MQTT Server

Minimal MQTT ingestion platform for Acoupi devices.

This repository contains:

- `Mosquitto` as the MQTT broker
- `PostgreSQL` for durable message storage
- a small Python ingest service that subscribes to MQTT and stores messages
- `Grafana` for a simple dashboard
- optional `MQTT Explorer` for live broker inspection

## Message model

- Each device publishes to its own MQTT topic.
- The MQTT topic is the canonical `device_id` stored by the server.
- Heartbeat messages may also contain a payload-level `device_id`; this is stored separately as `payload_device_id`.
- Detection and heartbeat messages can share the same device topic.
- Message type is inferred from payload structure.

## Services

- MQTT broker: `localhost:1883`
- Ingest health endpoint: `http://localhost:8000/health`
- Grafana: `http://localhost:3000`
- PostgreSQL: `localhost:5432`

The default deployment uses normal Docker bridge networking. Containers talk to each other by Compose service name, while the listed ports are published to the host.

## Quick start

1. Copy `.env.example` to `.env` and adjust credentials if needed.
2. Start the stack:

```bash
docker compose up --build
```

3. Open Grafana at `http://localhost:3000`.
4. Check the ingest service at `http://localhost:8000/health`.

Grafana now provisions two dashboards:

- `Acoupi System Overview` for operational monitoring
- `Acoupi Ecological Overview` for species and detection patterns

To include the optional MQTT Explorer UI:

```bash
docker compose --profile tools up --build
```

If you already have local services using ports `1883`, `3000`, `5432`, or `8000`, stop them first or change the container configuration before starting the stack.

If you change network settings in `docker-compose.yml`, recreate containers so Docker does not keep stale networking from older containers:

```bash
docker compose down --remove-orphans
docker compose up --build --force-recreate
```

## Grafana login

Default Grafana credentials:

- username: `admin`
- password: `admin`

These values come from `docker-compose.yml` and can be changed with environment variables in `.env`:

```env
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin
```

Recommended for any non-local deployment:

- change `GRAFANA_ADMIN_PASSWORD` before starting the stack
- restart Grafana after updating `.env`

## MQTT Explorer

MQTT Explorer is available as an optional service for live inspection of broker topics and messages.

Start it with the `tools` profile:

```bash
docker compose --profile tools up --build
```

Access it at:

- `http://localhost:3001`

Default MQTT Explorer login:

- username: `admin`
- password: `admin`

These values can be changed in `.env`:

```env
MQTT_EXPLORER_USERNAME=admin
MQTT_EXPLORER_PASSWORD=admin
```

How to connect MQTT Explorer to the broker:

1. Open `http://localhost:3001`
2. Log in with the configured MQTT Explorer credentials
3. Create a new broker connection
4. Use these broker settings:

- host: `mosquitto`
- port: `1883`
- username: leave empty unless MQTT auth is enabled later
- password: leave empty unless MQTT auth is enabled later

Notes:

- MQTT Explorer shows live broker traffic and topic structure
- Grafana shows stored historical data from PostgreSQL
- MQTT Explorer is optional and is not required for the ingestion pipeline

## Grafana dashboards

The default Grafana provisioning includes two dashboards:

### Acoupi System Overview

Use this for operational monitoring:

- heartbeat status history by device
- message activity by device
- latest heartbeat per device
- recent messages across all message types

### Acoupi Ecological Overview

Use this for ecological interpretation:

- detections per species per day
- detections per hour of day by species
- confidence threshold selector
- day selector for the hourly species panel

## Development

Install and run with `uv`:

```bash
uv sync
uv run uvicorn acoupi_mqtt_server.main:app --host 0.0.0.0 --port 8000
```

## Test publishers

Two small Python scripts are included under `scripts/` to publish valid test messages.

Send a heartbeat message:

```bash
uv run python scripts/send_test_heartbeat.py
```

Send a detection message:

```bash
uv run python scripts/send_test_detection.py
```

Generate a more realistic historical detection dataset and publish it now:

```bash
uv run python scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-001
```

Generate the same dataset to JSON files for inspection:

```bash
uv run python scripts/generate_detection_dataset.py --output-dir tmp/detection-dataset
```

Use both modes at once:

```bash
uv run python scripts/generate_detection_dataset.py --publish --output-dir tmp/detection-dataset
```

Useful overrides:

```bash
uv run python scripts/send_test_heartbeat.py --topic acoupi/my-device --payload-device-id raspi-007
uv run python scripts/send_test_detection.py --topic acoupi/my-device --model-name birdnet-v2
uv run python scripts/generate_detection_dataset.py --publish --days 10 --recordings-per-day 24 --topic acoupi/my-device
```

Expected behavior:

- both messages should be published to the same topic if you use the same `--topic`
- the stored canonical `device_id` should come from the topic
- the heartbeat message should also populate `payload_device_id`
- the detection message should be classified as `detection`
- the heartbeat message should be classified as `heartbeat`

The dataset generator is meant for dashboard design:

- all generated recordings belong to the same deployment
- recordings and message `created_on` timestamps are spread across earlier days
- payloads are still published now, which simulates delayed delivery after poor connectivity
- detections include species tags with varying confidence scores

## Stored fields

The main table is `mqtt_messages`.

Important columns:

- `topic`: original MQTT topic
- `device_id`: topic-derived canonical device identifier
- `payload_device_id`: payload-level heartbeat device identifier when present
- `message_type`: `heartbeat`, `detection`, or `null`
- `payload`: raw JSON payload
- `payload_text`: raw text for malformed JSON
- `received_at`: server receive time
- `event_timestamp`: payload timestamp when available

## Configuration

Environment variables are documented in `.env.example`.

The default topic derivation rule strips `DEVICE_TOPIC_PREFIX` from the front of the topic when present. Example:

- topic `acoupi/pi-001` with `DEVICE_TOPIC_PREFIX=acoupi/` becomes `device_id=pi-001`
- topic `customer-42/device-alpha` with an empty prefix becomes `device_id=customer-42/device-alpha`

## Specs

- `spec/spec-architecture-acoupi-mqtt-ingestion-platform.md`
- `spec/spec-data-acoupi-message-contracts.md`
