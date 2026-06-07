# Acoupi MQTT Server

An MQTT and Grafana telemetry stack to ingest, store, and visualise Acoupi device data and species observations.

This platform collects data from deployed Acoupi monitoring devices, stores the data in a relational database, and visualises both hardware performance and ecological observations.

---

## Repository Map

If you are exploring the codebase for the first time, here is where the components live:

- **`services/`**: The application components.
- `ingest/`: A Python service that listens for incoming device messages.
- `grafana/`: The visualisation dashboard layouts and provisioning configurations.
- `mosquitto/`: The MQTT broker that handles incoming network traffic.
- `postgres/`: The database that stores incoming messages and structured observations.

- **`scripts/`**: Helper tools to simulate and publish test data into the server.

---

## Quick Start

Get the entire stack running locally using Docker.

### 1. Setup Environment

Copy the example configuration file to create your local environment file:

```bash
cp .env.example .env
```

### 2. Launch the Platform

Start the background services:

```bash
docker compose up --build
```

### 3. Access the Dashboards

Once the containers finish loading, open a web browser to view the platform:

- **Grafana Dashboards:** [http://localhost:3000](https://www.google.com/search?q=http://localhost:3000) (Username: `admin` / Password: `admin`).

---

## Visualising Data

The platform includes five dashboards to analyse different aspects of the collected data:

- **Observations:** Track species detections over time, filter by specific species tags, and sort data by classification confidence scores.
- **Deployments:** Track where devices are deployed, including geographic distribution.
- **Recordings:** Monitor the specific audio files captured by the hardware, including file metadata and collection times.
- **Messages:** Used for operational monitoring.
  Track the volume of incoming data packets and see which devices are sending data.
- **Health:** Used for hardware maintenance.
  Check device heartbeats to ensure field equipment remains online.

---

## Testing with Mock Data

When you first launch the platform, the dashboards will be empty.
You can simulate active field equipment by running the included test scripts.

_(Requires Python and the `uv` package manager installed locally)_

**Publish a single sample heartbeat:**

```bash
uv run python scripts/send_test_heartbeat.py
```

**Publish a single sample species detection:**

```bash
uv run python scripts/send_test_detection.py
```

**Generate a simluated dataset:** This command generates a multi-day timeline of species observations into your local database for testing:

```bash
uv run python scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-001
```

---

## Advanced Tools & Development

### Modifying Dashboards

The Grafana dashboards are managed as code.
If you modify the dashboard layouts in the UI and want to save them back into the repository assets, regenerate them using:

```bash
just build-grafana
```
