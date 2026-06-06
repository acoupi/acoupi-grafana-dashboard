from __future__ import annotations

from collections.abc import Iterable

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool


class Database:
    def __init__(self, dsn: str) -> None:
        self.pool = ConnectionPool(
            conninfo=dsn, min_size=1, max_size=5, kwargs={"row_factory": dict_row}
        )

    def open(self) -> None:
        self.pool.open(wait=True)

    def close(self) -> None:
        self.pool.close()

    def ping(self) -> bool:
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return True

    def insert_message(self, record: dict) -> int:
        payload = Jsonb(record["payload"]) if record["payload"] is not None else None
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO mqtt_messages (
                        event_timestamp,
                        topic,
                        device_id,
                        payload_device_id,
                        message_type,
                        payload,
                        payload_text,
                        qos,
                        retain,
                        ingest_status,
                        reject_reason
                    ) VALUES (
                        %(event_timestamp)s,
                        %(topic)s,
                        %(device_id)s,
                        %(payload_device_id)s,
                        %(message_type)s,
                        %(payload)s,
                        %(payload_text)s,
                        %(qos)s,
                        %(retain)s,
                        %(ingest_status)s,
                        %(reject_reason)s
                    )
                    """,
                    {**record, "payload": payload},
                )
                cur.execute("SELECT lastval() AS id")
                message_id = cur.fetchone()["id"]
            conn.commit()
        if message_id is None:
            raise RuntimeError("failed to retrieve inserted mqtt_messages id")
        assert isinstance(message_id, int)
        return message_id

    def upsert_device(self, device_name: str, serial_number: str | None) -> int:
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO devices (device_name, serial_number)
                    VALUES (%(device_name)s, %(serial_number)s)
                    ON CONFLICT (device_name) DO UPDATE
                    SET serial_number = COALESCE(EXCLUDED.serial_number, devices.serial_number)
                    RETURNING id
                    """,
                    {"device_name": device_name, "serial_number": serial_number},
                )
                row = cur.fetchone()
            conn.commit()
        if row is None:
            raise RuntimeError("failed to upsert device")
        return row["id"]

    def upsert_deployment(self, deployment: dict) -> int:
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO deployments (
                        deployment_uuid,
                        device_id,
                        name,
                        latitude,
                        longitude,
                        elevation,
                        started_on,
                        ended_on
                    ) VALUES (
                        %(deployment_uuid)s,
                        %(device_id)s,
                        %(name)s,
                        %(latitude)s,
                        %(longitude)s,
                        %(elevation)s,
                        %(started_on)s,
                        %(ended_on)s
                    )
                    ON CONFLICT (deployment_uuid) DO UPDATE
                    SET device_id = EXCLUDED.device_id,
                        name = EXCLUDED.name,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        elevation = EXCLUDED.elevation,
                        started_on = EXCLUDED.started_on,
                        ended_on = EXCLUDED.ended_on
                    RETURNING id
                    """,
                    deployment,
                )
                row = cur.fetchone()
            conn.commit()
        if row is None:
            raise RuntimeError("failed to upsert deployment")
        return row["id"]

    def upsert_recording(self, recording: dict) -> int:
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO recordings (
                        recording_uuid,
                        deployment_id,
                        device_id,
                        message_id,
                        recorded_on,
                        duration_seconds,
                        sample_rate_hz,
                        audio_channels,
                        bit_depth
                    ) VALUES (
                        %(recording_uuid)s,
                        %(deployment_id)s,
                        %(device_id)s,
                        %(message_id)s,
                        %(recorded_on)s,
                        %(duration_seconds)s,
                        %(sample_rate_hz)s,
                        %(audio_channels)s,
                        %(bit_depth)s
                    )
                    ON CONFLICT (recording_uuid) DO UPDATE
                    SET deployment_id = EXCLUDED.deployment_id,
                        device_id = EXCLUDED.device_id,
                        message_id = EXCLUDED.message_id,
                        recorded_on = EXCLUDED.recorded_on,
                        duration_seconds = EXCLUDED.duration_seconds,
                        sample_rate_hz = EXCLUDED.sample_rate_hz,
                        audio_channels = EXCLUDED.audio_channels,
                        bit_depth = EXCLUDED.bit_depth
                    RETURNING id
                    """,
                    recording,
                )
                row = cur.fetchone()
            conn.commit()
        if row is None:
            raise RuntimeError("failed to upsert recording")
        return row["id"]

    def upsert_observation(self, observation: dict) -> int:
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO observations (
                        observation_uuid,
                        recording_id,
                        deployment_id,
                        device_id,
                        message_id,
                        recorded_on,
                        detection_score,
                        count,
                        event_start_seconds,
                        event_end_seconds,
                        frequency_low_hz,
                        frequency_high_hz,
                        classified_by
                    ) VALUES (
                        %(observation_uuid)s,
                        %(recording_id)s,
                        %(deployment_id)s,
                        %(device_id)s,
                        %(message_id)s,
                        %(recorded_on)s,
                        %(detection_score)s,
                        %(count)s,
                        %(event_start_seconds)s,
                        %(event_end_seconds)s,
                        %(frequency_low_hz)s,
                        %(frequency_high_hz)s,
                        %(classified_by)s
                    )
                    ON CONFLICT (observation_uuid) DO UPDATE
                    SET recording_id = EXCLUDED.recording_id,
                        deployment_id = EXCLUDED.deployment_id,
                        device_id = EXCLUDED.device_id,
                        message_id = EXCLUDED.message_id,
                        recorded_on = EXCLUDED.recorded_on,
                        detection_score = EXCLUDED.detection_score,
                        count = EXCLUDED.count,
                        event_start_seconds = EXCLUDED.event_start_seconds,
                        event_end_seconds = EXCLUDED.event_end_seconds,
                        frequency_low_hz = EXCLUDED.frequency_low_hz,
                        frequency_high_hz = EXCLUDED.frequency_high_hz,
                        classified_by = EXCLUDED.classified_by
                    RETURNING id
                    """,
                    observation,
                )
                row = cur.fetchone()
            conn.commit()
        if row is None:
            raise RuntimeError("failed to upsert observation")
        return row["id"]

    def replace_observation_tags(
        self, observation_id: int, tags: Iterable[dict]
    ) -> None:
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM observation_tags WHERE observation_id = %(observation_id)s",
                    {"observation_id": observation_id},
                )
                for tag in tags:
                    cur.execute(
                        """
                        INSERT INTO observation_tags (
                            observation_id,
                            tag_key,
                            tag_value,
                            confidence_score
                        ) VALUES (
                            %(observation_id)s,
                            %(tag_key)s,
                            %(tag_value)s,
                            %(confidence_score)s
                        )
                        ON CONFLICT (observation_id, tag_key, tag_value) DO UPDATE
                        SET confidence_score = EXCLUDED.confidence_score
                        """,
                        {"observation_id": observation_id, **tag},
                    )
            conn.commit()
