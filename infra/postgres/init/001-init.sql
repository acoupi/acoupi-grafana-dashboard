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

CREATE TABLE IF NOT EXISTS devices (
    id BIGSERIAL PRIMARY KEY,
    device_name TEXT NOT NULL UNIQUE,
    serial_number TEXT
);

CREATE TABLE IF NOT EXISTS deployments (
    id BIGSERIAL PRIMARY KEY,
    deployment_uuid UUID NOT NULL UNIQUE,
    device_id BIGINT NOT NULL REFERENCES devices(id),
    name TEXT NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    elevation DOUBLE PRECISION,
    started_on TIMESTAMPTZ NOT NULL,
    ended_on TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS recordings (
    id BIGSERIAL PRIMARY KEY,
    recording_uuid UUID NOT NULL UNIQUE,
    deployment_id BIGINT NOT NULL REFERENCES deployments(id),
    device_id BIGINT NOT NULL REFERENCES devices(id),
    message_id BIGINT NOT NULL REFERENCES mqtt_messages(id),
    recorded_on TIMESTAMPTZ NOT NULL,
    duration_seconds DOUBLE PRECISION NOT NULL,
    sample_rate_hz INTEGER NOT NULL,
    audio_channels INTEGER,
    bit_depth INTEGER
);

CREATE TABLE IF NOT EXISTS observations (
    id BIGSERIAL PRIMARY KEY,
    observation_uuid UUID NOT NULL UNIQUE,
    recording_id BIGINT NOT NULL REFERENCES recordings(id),
    deployment_id BIGINT NOT NULL REFERENCES deployments(id),
    device_id BIGINT NOT NULL REFERENCES devices(id),
    message_id BIGINT NOT NULL REFERENCES mqtt_messages(id),
    recorded_on TIMESTAMPTZ NOT NULL,
    detection_score DOUBLE PRECISION NOT NULL,
    count INTEGER,
    event_start_seconds DOUBLE PRECISION,
    event_end_seconds DOUBLE PRECISION,
    frequency_low_hz DOUBLE PRECISION,
    frequency_high_hz DOUBLE PRECISION,
    classified_by TEXT
);

CREATE TABLE IF NOT EXISTS observation_tags (
    id BIGSERIAL PRIMARY KEY,
    observation_id BIGINT NOT NULL REFERENCES observations(id) ON DELETE CASCADE,
    tag_key TEXT NOT NULL,
    tag_value TEXT NOT NULL,
    confidence_score DOUBLE PRECISION,
    UNIQUE (observation_id, tag_key, tag_value)
);

CREATE INDEX IF NOT EXISTS idx_devices_device_name ON devices (device_name);
CREATE INDEX IF NOT EXISTS idx_deployments_device_id ON deployments (device_id);
CREATE INDEX IF NOT EXISTS idx_deployments_started_on ON deployments (started_on DESC);
CREATE INDEX IF NOT EXISTS idx_recordings_device_id ON recordings (device_id);
CREATE INDEX IF NOT EXISTS idx_recordings_recorded_on ON recordings (recorded_on DESC);
CREATE INDEX IF NOT EXISTS idx_observations_device_id ON observations (device_id);
CREATE INDEX IF NOT EXISTS idx_observations_recorded_on ON observations (recorded_on DESC);
CREATE INDEX IF NOT EXISTS idx_observation_tags_key_value ON observation_tags (tag_key, tag_value);
