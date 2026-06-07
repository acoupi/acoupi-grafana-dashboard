from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    mqtt_host: str = Field(default="localhost", alias="MQTT_HOST")
    mqtt_port: int = Field(default=1883, alias="MQTT_PORT")
    mqtt_subscribe_topic: str = Field(default="#", alias="MQTT_SUBSCRIBE_TOPIC")
    mqtt_client_id: str = Field(default="acoupi-ingest", alias="MQTT_CLIENT_ID")
    mqtt_username: str | None = Field(default=None, alias="MQTT_USERNAME")
    mqtt_password: str | None = Field(default=None, alias="MQTT_PASSWORD")
    device_topic_prefix: str = Field(default="acoupi/", alias="DEVICE_TOPIC_PREFIX")
    database_url: str = Field(
        default="postgresql://acoupi:acoupi@localhost:5432/acoupi",
        alias="DATABASE_URL",
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")


settings = Settings()
