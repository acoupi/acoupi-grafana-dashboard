from __future__ import annotations

from scripts.grafana_dashboards_common import (
    grafana_dashboard,
    json_from_builder,
    set_table_defaults,
    set_targets,
    state_timeline_panel,
    table_panel,
    target,
)


def build_dashboard() -> dict:
    dashboard = grafana_dashboard(
        "Recordings V2",
        "acoupi-recordings-v2",
        ["acoupi", "recordings"],
        refresh="30s",
        time_from="now-30d",
        time_to="now",
        version=1,
    )
    panels = []

    coverage = json_from_builder(
        state_timeline_panel("Recording Coverage Per Device", 1, 14, 24, 0, 0)
    )
    coverage["options"] = {
        "columnWidth": 0.9,
        "legend": {"showLegend": False},
        "mergeValues": False,
        "rowHeight": 0.9,
        "showValue": "auto",
        "tooltip": {"mode": "single", "sort": "none"},
    }
    coverage["transformations"] = [
        {
            "id": "organize",
            "options": {
                "excludeByName": {},
                "indexByName": {"device": 0, "time": 1, "timeend": 2, "value": 3},
                "renameByName": {},
            },
        }
    ]
    set_targets(
        coverage,
        target(
            "table",
            "SELECT\n  recordings.recorded_on AS time,\n  recordings.recorded_on + make_interval(secs => recordings.duration_seconds) AS timeend,\n  devices.device_name AS device,\n  recordings.sample_rate_hz::text AS value\nFROM recordings\nJOIN devices ON devices.id = recordings.device_id\nWHERE recordings.recorded_on >= $__timeFrom()\n  AND recordings.recorded_on <= $__timeTo()\nORDER BY devices.device_name, recordings.recorded_on;",
        ),
    )
    panels.append(coverage)

    latest = json_from_builder(table_panel("Latest Recordings", 2, 12, 24, 0, 14))
    set_table_defaults(latest)
    set_targets(
        latest,
        target(
            "table",
            "SELECT\n  devices.device_name AS device,\n  recordings.recorded_on,\n  recordings.duration_seconds,\n  recordings.sample_rate_hz,\n  recordings.audio_channels,\n  recordings.bit_depth,\n  recordings.recording_uuid\nFROM recordings\nJOIN devices ON devices.id = recordings.device_id\nORDER BY recordings.recorded_on DESC\nLIMIT 20;",
        ),
    )
    panels.append(latest)

    dashboard["panels"] = panels
    return dashboard
