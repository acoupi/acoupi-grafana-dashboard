from __future__ import annotations

from grafana_foundation_sdk.builders import dashboard, statetimeline, table
from grafana_foundation_sdk.models.common import TableCellHeight, TimeZoneBrowser
from grafana_foundation_sdk.models.dashboard import (
    DashboardCursorSync,
    DataTransformerConfig,
    GridPos,
)

from scripts.grafana_dashboards_common import json_from_builder, postgres_ref
from scripts.grafana_sql_datasource import PostgresQueryBuilder

RECORDING_COVERAGE_SQL = """
SELECT
  recordings.recorded_on AS time,
  recordings.recorded_on + make_interval(secs => recordings.duration_seconds) AS timeend,
  devices.device_name AS device,
  recordings.sample_rate_hz::text AS value
FROM recordings
JOIN devices ON devices.id = recordings.device_id
WHERE recordings.recorded_on >= $__timeFrom()
  AND recordings.recorded_on <= $__timeTo()
ORDER BY devices.device_name, recordings.recorded_on;
"""


def build_recording_coverage_panel():
    return (
        statetimeline.Panel()
        .title("Recording Coverage Per Device")
        .id(1)
        .grid_pos(GridPos(h=14, w=24, x=0, y=0))
        .datasource(postgres_ref())
        .with_transformation(
            DataTransformerConfig(
                id_val="organize",
                options={
                    "excludeByName": {},
                    "indexByName": {"device": 0, "time": 1, "timeend": 2, "value": 3},
                    "renameByName": {},
                },
            )
        )
        .with_target(
            PostgresQueryBuilder()
            .query(RECORDING_COVERAGE_SQL)
            .datasource(postgres_ref())
            .format("table")
        )
    )
    # built = json_from_builder(panel)
    # built["options"] = {
    #     "columnWidth": 0.9,
    #     "legend": {"showLegend": False},
    #     "mergeValues": False,
    #     "rowHeight": 0.9,
    #     "showValue": "auto",
    #     "tooltip": {"mode": "single", "sort": "none"},
    # }


LATEST_RECORDINGS_SQL = """
SELECT
  devices.device_name AS device,
  recordings.recorded_on,
  recordings.duration_seconds,
  recordings.sample_rate_hz,
  recordings.audio_channels,
  recordings.bit_depth,
  recordings.recording_uuid
FROM recordings
JOIN devices ON devices.id = recordings.device_id
ORDER BY recordings.recorded_on DESC
LIMIT 20;
"""


def build_latest_recordings_panel() -> table.Panel:
    return (
        table.Panel()
        .title("Latest Recordings")
        .id(2)
        .grid_pos(GridPos(h=12, w=24, x=0, y=14))
        .datasource(postgres_ref())
        .show_header(True)
        .cell_height(TableCellHeight.SM)
        .with_target(
            PostgresQueryBuilder()
            .query(LATEST_RECORDINGS_SQL)
            .datasource(postgres_ref())
            .format("table")
        )
    )


def build_dashboard() -> dict:
    dash = (
        dashboard.Dashboard("Recordings")
        .uid("acoupi-recordings")
        .tags(["acoupi", "recordings"])
        .refresh("30s")
        .style("dark")
        .timezone(TimeZoneBrowser)
        .time("now-30d", "now")
        .tooltip(DashboardCursorSync.OFF)
        .editable()
        .version(1)
        .with_panel(build_recording_coverage_panel())
        .with_panel(build_latest_recordings_panel())
    )
    return json_from_builder(dash)
