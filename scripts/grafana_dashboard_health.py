from __future__ import annotations

from grafana_foundation_sdk.builders import dashboard, table, timeseries
from grafana_foundation_sdk.models.common import (
    GraphDrawStyle,
    LineInterpolation,
    TableCellHeight,
    TimeZoneBrowser,
    VisibilityMode,
)
from grafana_foundation_sdk.models.dashboard import DashboardCursorSync, GridPos

from scripts.grafana_dashboards_common import (
    classic_palette,
    default_legend,
    json_from_builder,
    postgres_ref,
    single_tooltip,
)
from scripts.grafana_sql_datasource import PostgresQueryBuilder

HEARTBEATS_BY_DEVICE_SQL = """
WITH device_rows AS (
  SELECT
    device_id,
    dense_rank() OVER (ORDER BY device_id) AS row_index
  FROM (SELECT DISTINCT device_id FROM mqtt_messages WHERE message_type = 'heartbeat' AND ingest_status = 'accepted') devices
)
SELECT
  m.received_at AS time,
  m.device_id AS metric,
  d.row_index::double precision AS value
FROM mqtt_messages m
JOIN device_rows d ON d.device_id = m.device_id
WHERE m.message_type = 'heartbeat'
  AND m.ingest_status = 'accepted'
  AND $__timeFilter(m.received_at)
ORDER BY m.received_at;
"""


def build_heartbeats_by_device_panel() -> timeseries.Panel:
    return (
        timeseries.Panel()
        .title("Heartbeats By Device")
        .id(1)
        .grid_pos(GridPos(h=8, w=24, x=0, y=0))
        .datasource(postgres_ref())
        .color_scheme(classic_palette())
        .legend(default_legend())
        .tooltip(single_tooltip())
        .draw_style(GraphDrawStyle.POINTS)
        .line_interpolation(LineInterpolation.LINEAR)
        .line_width(0)
        .point_size(8)
        .show_points(VisibilityMode.ALWAYS)
        .span_nulls(False)
        .min(0)
        .with_target(
            PostgresQueryBuilder()
            .query(HEARTBEATS_BY_DEVICE_SQL)
            .datasource(postgres_ref())
            .format("time_series")
        )
    )


LATEST_HEARTBEAT_PER_DEVICE_SQL = """
SELECT DISTINCT ON (device_id)
  device_id,
  received_at,
  payload_device_id,
  COALESCE(payload->>'status', 'UNKNOWN') AS status,
  topic
FROM mqtt_messages
WHERE message_type = 'heartbeat'
  AND ingest_status = 'accepted'
ORDER BY device_id, received_at DESC;
"""


def build_latest_heartbeat_per_device_panel() -> table.Panel:
    return (
        table.Panel()
        .title("Latest Heartbeat Per Device")
        .id(2)
        .grid_pos(GridPos(h=12, w=24, x=0, y=8))
        .datasource(postgres_ref())
        .show_header(True)
        .cell_height(TableCellHeight.SM)
        .with_target(
            PostgresQueryBuilder()
            .query(LATEST_HEARTBEAT_PER_DEVICE_SQL)
            .datasource(postgres_ref())
            .format("table")
        )
    )


def build_dashboard() -> dict:
    dash = (
        dashboard.Dashboard("Health")
        .uid("acoupi-health")
        .tags(["acoupi", "health"])
        .refresh("30s")
        .style("dark")
        .timezone(TimeZoneBrowser)
        .time("now-24h", "now")
        .tooltip(DashboardCursorSync.OFF)
        .editable()
        .version(1)
        .with_panel(build_heartbeats_by_device_panel())
        .with_panel(build_latest_heartbeat_per_device_panel())
    )

    return json_from_builder(dash)
