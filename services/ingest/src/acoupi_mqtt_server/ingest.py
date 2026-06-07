from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

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


def safe_uuid(value: str | None) -> UUID | None:
    if not value:
        return None
    return UUID(value)


def extract_bit_depth(payload: dict[str, Any]) -> int | None:
    value = payload.get("bit_depth")
    if isinstance(value, int):
        return value
    return None


def normalize_detection_payload(
    database: Database,
    message_id: int,
    device_name: str,
    payload: dict[str, Any],
) -> None:
    device_row_id = database.upsert_device(device_name, None)

    deployment_payload = payload["recording"]["deployment"]
    deployment_id = database.upsert_deployment(
        {
            "deployment_uuid": safe_uuid(deployment_payload["id"]),
            "device_id": device_row_id,
            "name": deployment_payload["name"],
            "latitude": deployment_payload.get("latitude"),
            "longitude": deployment_payload.get("longitude"),
            "elevation": deployment_payload.get("elevation"),
            "started_on": deployment_payload["started_on"],
            "ended_on": deployment_payload.get("ended_on"),
        }
    )

    recording_payload = payload["recording"]
    recording_id = database.upsert_recording(
        {
            "recording_uuid": safe_uuid(recording_payload["id"]),
            "deployment_id": deployment_id,
            "device_id": device_row_id,
            "message_id": message_id,
            "recorded_on": recording_payload["created_on"],
            "duration_seconds": recording_payload["duration"],
            "sample_rate_hz": recording_payload["samplerate"],
            "audio_channels": recording_payload.get("audio_channels"),
            "bit_depth": extract_bit_depth(recording_payload),
        }
    )

    for detection in payload.get("detections", []):
        coordinates = None
        if isinstance(detection.get("location"), dict):
            raw_coordinates = detection["location"].get("coordinates")
            if isinstance(raw_coordinates, list | tuple) and len(raw_coordinates) == 4:
                coordinates = raw_coordinates

        observation_id = database.upsert_observation(
            {
                "observation_uuid": safe_uuid(detection["id"]),
                "recording_id": recording_id,
                "deployment_id": deployment_id,
                "device_id": device_row_id,
                "message_id": message_id,
                "recorded_on": recording_payload["created_on"],
                "detection_score": detection.get("detection_score", 1.0),
                "count": detection.get("count"),
                "event_start_seconds": coordinates[0] if coordinates else None,
                "event_end_seconds": coordinates[2] if coordinates else None,
                "frequency_low_hz": coordinates[1] if coordinates else None,
                "frequency_high_hz": coordinates[3] if coordinates else None,
                "classified_by": payload.get("name_model"),
            }
        )

        database.replace_observation_tags(
            observation_id,
            [
                {
                    "tag_key": predicted_tag["tag"]["key"],
                    "tag_value": predicted_tag["tag"]["value"],
                    "confidence_score": predicted_tag.get("confidence_score"),
                }
                for predicted_tag in detection.get("tags", [])
                if isinstance(predicted_tag.get("tag"), dict)
                and isinstance(predicted_tag["tag"].get("key"), str)
                and isinstance(predicted_tag["tag"].get("value"), str)
            ],
        )


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
        self.client = mqtt.Client(client_id=settings.mqtt_client_id)
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
        userdata: object,
        flags: object,
        reason_code: object,
        properties: object | None = None,
    ) -> None:
        self.connected = True
        logger.info(
            "connected to MQTT broker with reason code %s; subscribing to %s",
            reason_code,
            self.settings.mqtt_subscribe_topic,
        )
        client.subscribe(self.settings.mqtt_subscribe_topic)

    def on_disconnect(
        self,
        client: mqtt.Client,
        userdata: object,
        disconnect_flags: object,
        reason_code: object,
        properties: object | None = None,
    ) -> None:
        self.connected = False
        logger.warning("disconnected from MQTT broker with reason code %s", reason_code)

    def on_message(
        self, client: mqtt.Client, userdata: object, message: mqtt.MQTTMessage
    ) -> None:
        topic = message.topic
        canonical_device_id = derive_device_id(topic, self.settings.device_topic_prefix)
        classified = classify_payload(message.payload)

        message_id = self.database.insert_message(
            {
                "event_timestamp": classified.event_timestamp,
                "topic": topic,
                "device_id": canonical_device_id,
                "payload_device_id": classified.payload_device_id,
                "message_type": classified.message_type,
                "payload": classified.payload,
                "payload_text": classified.payload_text,
                "qos": message.qos,
                "retain": message.retain,
                "ingest_status": classified.ingest_status,
                "reject_reason": classified.reject_reason,
            }
        )

        if classified.ingest_status != "accepted" or classified.payload is None:
            logger.info(
                "stored MQTT message %s topic=%s device_id=%s status=%s reason=%s",
                message_id,
                topic,
                canonical_device_id,
                classified.ingest_status,
                classified.reject_reason,
            )
            return

        if classified.message_type == "detection":
            normalize_detection_payload(
                self.database, message_id, canonical_device_id, classified.payload
            )

        logger.info(
            "stored MQTT message %s topic=%s device_id=%s payload_device_id=%s type=%s status=%s",
            message_id,
            topic,
            canonical_device_id,
            classified.payload_device_id,
            classified.message_type,
            classified.ingest_status,
        )
