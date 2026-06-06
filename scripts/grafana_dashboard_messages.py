from __future__ import annotations

from scripts.grafana_dashboards_common import (
    grafana_dashboard,
    json_from_builder,
    point_timeseries_panel,
    set_table_defaults,
    set_targets,
    table_panel,
    target,
    timeseries_panel,
)


def build_dashboard() -> dict:
    dashboard = grafana_dashboard(
        "Messages V2",
        "acoupi-messages-v2",
        ["acoupi", "messages"],
        refresh="30s",
        time_from="now-24h",
        time_to="now",
        version=1,
    )
    panels = []

    messages_over_time = json_from_builder(
        timeseries_panel("Messages Over Time", 1, 8, 24, 0, 0)
    )
    set_targets(
        messages_over_time,
        target(
            "time_series",
            "SELECT $__timeGroupAlias(received_at, '1m'), COUNT(*)::double precision AS value\nFROM mqtt_messages\nWHERE $__timeFilter(received_at)\nGROUP BY 1\nORDER BY 1;",
        ),
    )
    panels.append(messages_over_time)

    activity_by_device = json_from_builder(
        point_timeseries_panel("Message Activity By Device", 3, 8, 24, 0, 8)
    )
    set_targets(
        activity_by_device,
        target(
            "time_series",
            "WITH device_rows AS (\n  SELECT\n    device_id,\n    dense_rank() OVER (ORDER BY device_id) AS row_index\n  FROM (SELECT DISTINCT device_id FROM mqtt_messages) devices\n)\nSELECT\n  m.received_at AS time,\n  m.device_id AS metric,\n  d.row_index::double precision AS value\nFROM mqtt_messages m\nJOIN device_rows d ON d.device_id = m.device_id\nWHERE $__timeFilter(m.received_at)\nORDER BY m.received_at;",
        ),
    )
    panels.append(activity_by_device)

    recent_messages = json_from_builder(
        table_panel("Recent Messages", 5, 12, 24, 0, 16)
    )
    set_table_defaults(recent_messages)
    set_targets(
        recent_messages,
        target(
            "table",
            "SELECT received_at, device_id, payload_device_id, message_type, topic, ingest_status\nFROM mqtt_messages\nORDER BY received_at DESC\nLIMIT 100;",
        ),
    )
    panels.append(recent_messages)

    dashboard["panels"] = panels
    return dashboard
