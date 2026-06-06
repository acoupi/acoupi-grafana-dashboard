from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI

from acoupi_mqtt_server.config import settings
from acoupi_mqtt_server.database import Database
from acoupi_mqtt_server.ingest import MqttIngestService


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

database = Database(settings.database_url)
ingest_service = MqttIngestService(settings, database)


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.open()
    ingest_service.start()
    try:
        yield
    finally:
        ingest_service.stop()
        database.close()


app = FastAPI(title="Acoupi MQTT Ingest Service", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, object]:
    database_connected = False
    try:
        database_connected = database.ping()
    except Exception:
        logging.getLogger(__name__).exception("database health check failed")

    return {
        "status": "ok"
        if database_connected and ingest_service.connected
        else "degraded",
        "mqtt_connected": ingest_service.connected,
        "database_connected": database_connected,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
