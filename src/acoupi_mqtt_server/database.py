from __future__ import annotations

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

    def insert_message(self, record: dict) -> None:
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
            conn.commit()
