from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import paho.mqtt.client as mqtt
from pydantic import ValidationError

from acoupi_mqtt_server.config import Settings
from acoupi_mqtt_server.database import Database
from acoupi_mqtt_server.models import Heartbeat, ModelOutput


logger = logging.getLogger(__name__)


@dataclass
class ClassifiedMessage:
    message_type: str | None
    event_timestamp: datetime | None
    payload_device_id: str | None
    ingest_status: str
    reject_reason: str | None
    payload: dict[str, Any] | None
    payload_text: str | None


def derive_device_id(topic: str, topic_prefix: str) -> str:
    normalized_prefix = topic_prefix.strip()
    if normalized_prefix and topic.startswith(normalized_prefix):
        suffix = topic[len(normalized_prefix) :]
        return suffix or topic
    return topic


def classify_payload(raw_payload: bytes) -> ClassifiedMessage:
    try:
        decoded_text = raw_payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        return ClassifiedMessage(
            message_type=None,
            event_timestamp=None,
            payload_device_id=None,
            ingest_status="rejected",
            reject_reason=f"payload is not valid UTF-8: {exc}",
            payload=None,
            payload_text=None,
        )

    try:
        data = json.loads(decoded_text)
    except json.JSONDecodeError as exc:
        return ClassifiedMessage(
            message_type=None,
            event_timestamp=None,
            payload_device_id=None,
            ingest_status="rejected",
            reject_reason=f"payload is not valid JSON: {exc}",
            payload=None,
            payload_text=decoded_text,
        )

    if not isinstance(data, dict):
        return ClassifiedMessage(
            message_type=None,
            event_timestamp=None,
            payload_device_id=None,
            ingest_status="unknown",
            reject_reason="JSON payload is not an object",
            payload={"value": data},
            payload_text=None,
        )

    try:
        detection = ModelOutput.model_validate(data)
        return ClassifiedMessage(
            message_type="detection",
            event_timestamp=detection.created_on,
            payload_device_id=None,
            ingest_status="accepted",
            reject_reason=None,
            payload=data,
            payload_text=None,
        )
    except ValidationError:
        pass

    try:
        heartbeat = Heartbeat.model_validate(data)
        return ClassifiedMessage(
            message_type="heartbeat",
            event_timestamp=heartbeat.sent_on,
            payload_device_id=heartbeat.device_id,
            ingest_status="accepted",
            reject_reason=None,
            payload=data,
            payload_text=None,
        )
    except ValidationError:
        return ClassifiedMessage(
            message_type=None,
            event_timestamp=None,
            payload_device_id=data.get("device_id")
            if isinstance(data.get("device_id"), str)
            else None,
            ingest_status="unknown",
            reject_reason="JSON payload did not match heartbeat or detection schema",
            payload=data,
            payload_text=None,
        )


class MqttIngestService:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings = settings
        self.database = database
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2, client_id=settings.mqtt_client_id
        )
        self.connected = False

        if settings.mqtt_username:
            self.client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

    def start(self) -> None:
        logger.info(
            "connecting to MQTT broker at %s:%s",
            self.settings.mqtt_host,
            self.settings.mqtt_port,
        )
        self.client.connect(
            self.settings.mqtt_host, self.settings.mqtt_port, keepalive=60
        )
        self.client.loop_start()

    def stop(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()

    def on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Any,
        reason_code: Any,
        properties: Any,
    ) -> None:
        self.connected = True
        logger.info(
            "connected to MQTT broker, subscribing to %s",
            self.settings.mqtt_subscribe_topic,
        )
        client.subscribe(self.settings.mqtt_subscribe_topic)

    def on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        disconnect_flags: Any,
        reason_code: Any,
        properties: Any,
    ) -> None:
        self.connected = False
        logger.warning("disconnected from MQTT broker: %s", reason_code)

    def on_message(
        self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage
    ) -> None:
        classified = classify_payload(msg.payload)
        device_id = derive_device_id(msg.topic, self.settings.device_topic_prefix)

        record = {
            "event_timestamp": classified.event_timestamp,
            "topic": msg.topic,
            "device_id": device_id,
            "payload_device_id": classified.payload_device_id,
            "message_type": classified.message_type,
            "payload": classified.payload,
            "payload_text": classified.payload_text,
            "qos": msg.qos,
            "retain": bool(msg.retain),
            "ingest_status": classified.ingest_status,
            "reject_reason": classified.reject_reason,
        }

        try:
            self.database.insert_message(record)
        except Exception:
            logger.exception("failed to persist MQTT message from topic %s", msg.topic)
            return

        logger.info(
            "stored MQTT message topic=%s device_id=%s message_type=%s status=%s",
            msg.topic,
            device_id,
            classified.message_type,
            classified.ingest_status,
        )
