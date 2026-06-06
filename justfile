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
    uv run python scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-004 --days 30 --recordings-per-day 24 --seed 44

populate-more:
    uv run python scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-011 --days 30 --recordings-per-day 24 --seed 11
    uv run python scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-012 --days 30 --recordings-per-day 24 --seed 12
    uv run python scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-013 --days 30 --recordings-per-day 24 --seed 13
    uv run python scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-014 --days 30 --recordings-per-day 24 --seed 14
    uv run python scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-015 --days 30 --recordings-per-day 24 --seed 15
    uv run python scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-016 --days 30 --recordings-per-day 24 --seed 16
    uv run python scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-017 --days 30 --recordings-per-day 24 --seed 17
    uv run python scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-018 --days 30 --recordings-per-day 24 --seed 18

beat:
    uv run python scripts/send_test_heartbeat.py --topic acoupi/test-device-001
    uv run python scripts/send_test_heartbeat.py --topic acoupi/test-device-003

build-grafana:
    uv run python -m scripts.generate_grafana_dashboards

restart-grafana:
    docker compose restart grafana

reload-grafana: build-grafana restart-grafana
