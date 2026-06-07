build: build-grafana
    docker compose --profile tools up --build

up:
    docker compose --profile tools up

down:
    docker compose --profile tools down

clean:
    docker compose --profile tools down --remove-orphans -v

populate:
    uv run scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-001 --days 30 --recordings-per-day 24 --seed 11 --username admin --password admin
    uv run scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-002 --days 30 --recordings-per-day 24 --seed 22 --username admin --password admin
    uv run scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-003 --days 30 --recordings-per-day 24 --seed 33 --username admin --password admin
    uv run scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-004 --days 30 --recordings-per-day 24 --seed 44 --username admin --password admin

populate-more:
    uv run scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-011 --days 30 --recordings-per-day 24 --seed 11 --username admin --password admin
    uv run scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-012 --days 30 --recordings-per-day 24 --seed 12 --username admin --password admin
    uv run scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-013 --days 30 --recordings-per-day 24 --seed 13 --username admin --password admin
    uv run scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-014 --days 30 --recordings-per-day 24 --seed 14 --username admin --password admin
    uv run scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-015 --days 30 --recordings-per-day 24 --seed 15 --username admin --password admin
    uv run scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-016 --days 30 --recordings-per-day 24 --seed 16 --username admin --password admin
    uv run scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-017 --days 30 --recordings-per-day 24 --seed 17 --username admin --password admin
    uv run scripts/generate_detection_dataset.py --publish --topic acoupi/test-device-018 --days 30 --recordings-per-day 24 --seed 18 --username admin --password admin

beat:
    uv run scripts/send_test_heartbeat.py --topic acoupi/test-device-001 --username admin --password admin
    uv run scripts/send_test_heartbeat.py --topic acoupi/test-device-003 --username admin --password admin

build-grafana:
    cd services/grafana && just build

restart-grafana:
    docker compose restart grafana

reload-grafana: build-grafana restart-grafana

prod:
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build
