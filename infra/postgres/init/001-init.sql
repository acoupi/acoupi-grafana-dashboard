CREATE TABLE IF NOT EXISTS mqtt_messages (
    id BIGSERIAL PRIMARY KEY,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_timestamp TIMESTAMPTZ,
    topic TEXT NOT NULL,
    device_id TEXT NOT NULL,
    payload_device_id TEXT,
    message_type TEXT,
    payload JSONB,
    payload_text TEXT,
    qos INTEGER NOT NULL,
    retain BOOLEAN NOT NULL,
    ingest_status TEXT NOT NULL CHECK (ingest_status IN ('accepted', 'rejected', 'unknown')),
    reject_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_mqtt_messages_received_at ON mqtt_messages (received_at DESC);
CREATE INDEX IF NOT EXISTS idx_mqtt_messages_event_timestamp ON mqtt_messages (event_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_mqtt_messages_device_id ON mqtt_messages (device_id);
CREATE INDEX IF NOT EXISTS idx_mqtt_messages_message_type ON mqtt_messages (message_type);
CREATE INDEX IF NOT EXISTS idx_mqtt_messages_topic ON mqtt_messages (topic);
