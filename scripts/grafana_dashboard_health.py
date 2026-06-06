from __future__ import annotations

from scripts.grafana_dashboards_common import (
    grafana_dashboard,
    json_from_builder,
    point_timeseries_panel,
    set_table_defaults,
    set_targets,
    table_panel,
    target,
)


def build_dashboard() -> dict:
    dashboard = grafana_dashboard(
        "Health V2",
        "acoupi-health-v2",
        ["acoupi", "health"],
        refresh="30s",
        time_from="now-24h",
        time_to="now",
        version=1,
    )
    panels = []

    heartbeats = json_from_builder(
        point_timeseries_panel("Heartbeats By Device", 1, 8, 24, 0, 0)
    )
    set_targets(
        heartbeats,
        target(
            "time_series",
            "WITH device_rows AS (\n  SELECT\n    device_id,\n    dense_rank() OVER (ORDER BY device_id) AS row_index\n  FROM (SELECT DISTINCT device_id FROM mqtt_messages WHERE message_type = 'heartbeat' AND ingest_status = 'accepted') devices\n)\nSELECT\n  m.received_at AS time,\n  m.device_id AS metric,\n  d.row_index::double precision AS value\nFROM mqtt_messages m\nJOIN device_rows d ON d.device_id = m.device_id\nWHERE m.message_type = 'heartbeat'\n  AND m.ingest_status = 'accepted'\n  AND $__timeFilter(m.received_at)\nORDER BY m.received_at;",
        ),
    )
    panels.append(heartbeats)

    latest = json_from_builder(
        table_panel("Latest Heartbeat Per Device", 2, 12, 24, 0, 8)
    )
    set_table_defaults(latest)
    set_targets(
        latest,
        target(
            "table",
            "SELECT DISTINCT ON (device_id)\n  device_id,\n  received_at,\n  payload_device_id,\n  COALESCE(payload->>'status', 'UNKNOWN') AS status,\n  topic\nFROM mqtt_messages\nWHERE message_type = 'heartbeat'\n  AND ingest_status = 'accepted'\nORDER BY device_id, received_at DESC;",
        ),
    )
    panels.append(latest)

    dashboard["panels"] = panels
    return dashboard
