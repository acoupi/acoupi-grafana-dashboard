import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI

from acoupi_mqtt_server.config import settings
from acoupi_mqtt_server.database import Database
from acoupi_mqtt_server.ingest import MqttIngestService

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
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


app = FastAPI(title="Acoupi MQTT Ingest", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "mqtt_connected": str(ingest_service.connected).lower(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
