build: build-grafana
    docker compose --profile tools up --build

up:
    docker compose --profile tools up

down:
    docker compose --profile tools down

clean:
    docker compose --profile tools down --remove-orphans -v

populate:
    uv run python scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-001 --days 30 --recordings-per-day 24 --seed 1
    uv run python scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-002 --days 30 --recordings-per-day 24 --seed 2
    uv run python scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-003 --days 30 --recordings-per-day 24 --seed 3
    uv run python scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-004 --days 30 --recordings-per-day 24 --seed 4

beat:
    uv run python scripts/send_test_heartbeat.py --topic acoupi/test-device-001
    uv run python scripts/send_test_heartbeat.py --topic acoupi/test-device-003

build-grafana:
    uv run python -m scripts.generate_grafana_dashboards

restart-grafana:
    docker compose restart grafana

reload-grafana: build-grafana restart-grafana
