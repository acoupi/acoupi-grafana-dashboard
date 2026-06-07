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

MESSAGES_OVER_TIME_SQL = """
SELECT $__timeGroupAlias(received_at, '1m'), COUNT(*)::double precision AS value
FROM mqtt_messages
WHERE $__timeFilter(received_at)
GROUP BY 1
ORDER BY 1;
"""


def build_messages_over_time_panel() -> timeseries.Panel:
    return (
        timeseries.Panel()
        .title("Messages Over Time")
        .description("Shows total MQTT messages received over time.")
        .id(1)
        .grid_pos(GridPos(h=8, w=24, x=0, y=0))
        .datasource(postgres_ref())
        .color_scheme(classic_palette())
        .legend(default_legend())
        .tooltip(single_tooltip())
        .with_target(
            PostgresQueryBuilder()
            .query(MESSAGES_OVER_TIME_SQL)
            .datasource(postgres_ref())
            .format("time_series")
        )
    )


MESSAGE_ACTIVITY_BY_DEVICE_SQL = """
WITH device_rows AS (
  SELECT
    device_id,
    dense_rank() OVER (ORDER BY device_id) AS row_index
  FROM (SELECT DISTINCT device_id FROM mqtt_messages) devices
)
SELECT
  m.received_at AS time,
  m.device_id AS metric,
  d.row_index::double precision AS value
FROM mqtt_messages m
JOIN device_rows d ON d.device_id = m.device_id
WHERE $__timeFilter(m.received_at)
ORDER BY m.received_at;
"""


def build_message_activity_by_device_panel() -> timeseries.Panel:
    return (
        timeseries.Panel()
        .title("Message Activity By Device")
        .description("Shows when each device sent MQTT messages.")
        .id(3)
        .grid_pos(GridPos(h=8, w=24, x=0, y=8))
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
            .query(MESSAGE_ACTIVITY_BY_DEVICE_SQL)
            .datasource(postgres_ref())
            .format("time_series")
        )
    )


RECENT_MESSAGES_SQL = """
SELECT received_at, device_id, payload_device_id, message_type, topic, ingest_status
FROM mqtt_messages
ORDER BY received_at DESC
LIMIT 100;
"""


def build_recent_messages_panel() -> table.Panel:
    return (
        table.Panel()
        .title("Recent Messages")
        .description("Lists the most recently ingested MQTT messages.")
        .id(5)
        .grid_pos(GridPos(h=12, w=24, x=0, y=16))
        .datasource(postgres_ref())
        .show_header(True)
        .cell_height(TableCellHeight.SM)
        .with_target(
            PostgresQueryBuilder()
            .query(RECENT_MESSAGES_SQL)
            .datasource(postgres_ref())
            .format("table")
        )
    )


def build_dashboard() -> dict:
    dash = (
        dashboard.Dashboard("Messages")
        .uid("acoupi-messages")
        .tags(["acoupi", "messages"])
        .refresh("30s")
        .style("dark")
        .timezone(TimeZoneBrowser)
        .time("now-24h", "now")
        .tooltip(DashboardCursorSync.OFF)
        .editable()
        .version(1)
        .with_panel(build_messages_over_time_panel())
        .with_panel(build_message_activity_by_device_panel())
        .with_panel(build_recent_messages_panel())
    )

    return json_from_builder(dash)
