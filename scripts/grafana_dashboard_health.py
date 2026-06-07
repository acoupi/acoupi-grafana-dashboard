from __future__ import annotations

from grafana_foundation_sdk.builders import dashboard, stat, table, timeseries
from grafana_foundation_sdk.builders.common import ReduceDataOptions
from grafana_foundation_sdk.builders.dashboard import ThresholdsConfig
from grafana_foundation_sdk.models.common import (
    BigValueColorMode,
    BigValueGraphMode,
    BigValueJustifyMode,
    BigValueTextMode,
    GraphDrawStyle,
    LineInterpolation,
    TableCellHeight,
    TimeZoneBrowser,
    VisibilityMode,
    VizOrientation,
)
from grafana_foundation_sdk.models.dashboard import (
    DashboardCursorSync,
    DynamicConfigValue,
    GridPos,
    Threshold,
    VariableHide,
    VariableOption,
    VariableRefresh,
    VariableSort,
)

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


TOTAL_DEVICES_SQL = """
SELECT COUNT(*)::double precision AS value
FROM devices;
"""


def build_total_devices_panel() -> stat.Panel:
    return (
        stat.Panel()
        .title("Devices")
        .id(10)
        .grid_pos(GridPos(h=4, w=12, x=0, y=0))
        .datasource(postgres_ref())
        .color_mode(BigValueColorMode.NONE)
        .graph_mode(BigValueGraphMode.NONE)
        .justify_mode(BigValueJustifyMode.CENTER)
        .orientation(VizOrientation.AUTO)
        .text_mode(BigValueTextMode.VALUE)
        .reduce_options(ReduceDataOptions().values(False).calcs(["lastNotNull"]))
        .with_target(
            PostgresQueryBuilder()
            .query(TOTAL_DEVICES_SQL)
            .datasource(postgres_ref())
            .format("table")
        )
    )


UNHEALTHY_DEVICES_SQL = """
WITH latest_heartbeats AS (
  SELECT
    device_id,
    MAX(received_at) AS last_heartbeat_at
  FROM mqtt_messages
  WHERE message_type = 'heartbeat'
    AND ingest_status = 'accepted'
  GROUP BY device_id
)
SELECT COUNT(*)::double precision AS value
FROM devices
LEFT JOIN latest_heartbeats ON latest_heartbeats.device_id = devices.device_name
WHERE latest_heartbeats.last_heartbeat_at IS NULL
   OR latest_heartbeats.last_heartbeat_at < NOW() - INTERVAL '6 hours';
"""


DEVICE_CARD_SQL = """
SELECT device_name AS __value, device_name AS __text
FROM devices
ORDER BY device_name;
"""


def build_device_card_variable():
    return (
        dashboard.QueryVariable("device_card")
        .id("device_card")
        .label("Device Cards")
        .datasource(postgres_ref())
        .hide(VariableHide.HIDE_VARIABLE)
        .include_all(True)
        .multi(True)
        .current(VariableOption(selected=True, text="All", value="$__all"))
        .query(DEVICE_CARD_SQL)
        .refresh(VariableRefresh.ON_DASHBOARD_LOAD)
        .sort(VariableSort.ALPHABETICAL_ASC)
        .options([])
    )


DEVICE_HEALTH_CARD_SQL = """
WITH requested_device AS (
  SELECT ${device_card:sqlstring} AS device_name
), latest_heartbeat AS (
  SELECT MAX(received_at) AS last_heartbeat_at
  FROM mqtt_messages
  WHERE message_type = 'heartbeat'
    AND ingest_status = 'accepted'
    AND device_id = ${device_card:sqlstring}
)
SELECT
  requested_device.device_name AS device,
  CASE
    WHEN last_heartbeat_at IS NOT NULL AND last_heartbeat_at >= NOW() - INTERVAL '6 hours' THEN 1
    ELSE 0
  END AS healthy,
  CASE
    WHEN last_heartbeat_at IS NOT NULL AND last_heartbeat_at >= NOW() - INTERVAL '6 hours' THEN 'Healthy'
    ELSE 'Unhealthy'
  END AS status,
  last_heartbeat_at AS last_heartbeat
FROM requested_device
CROSS JOIN latest_heartbeat;
"""


def build_device_health_card_panel() -> table.Panel:
    return (
        table.Panel()
        .title("${device_card}")
        .id(12)
        .grid_pos(GridPos(h=5, w=6, x=0, y=24))
        .datasource(postgres_ref())
        .show_header(True)
        .cell_height(TableCellHeight.SM)
        .repeat("device_card")
        .repeat_direction("h")
        .override_by_name(
            "healthy",
            [
                DynamicConfigValue(id_val="custom.hidden", value=True),
            ],
        )
        .override_by_name(
            "status",
            [
                DynamicConfigValue(
                    id_val="mappings",
                    value=[
                        {
                            "type": "value",
                            "options": {
                                "Healthy": {"text": "Healthy", "color": "green"},
                                "Unhealthy": {"text": "Unhealthy", "color": "red"},
                            },
                        }
                    ],
                ),
                DynamicConfigValue(
                    id_val="custom.cellOptions",
                    value={"type": "color-text"},
                ),
            ],
        )
        .override_by_name(
            "last_heartbeat",
            [
                DynamicConfigValue(id_val="custom.width", value=220),
            ],
        )
        .with_target(
            PostgresQueryBuilder()
            .query(DEVICE_HEALTH_CARD_SQL)
            .datasource(postgres_ref())
            .format("table")
        )
    )


def build_unhealthy_devices_panel() -> stat.Panel:
    return (
        stat.Panel()
        .title("Unhealthy Devices")
        .id(11)
        .grid_pos(GridPos(h=4, w=12, x=12, y=0))
        .datasource(postgres_ref())
        .color_mode(BigValueColorMode.NONE)
        .graph_mode(BigValueGraphMode.NONE)
        .justify_mode(BigValueJustifyMode.CENTER)
        .orientation(VizOrientation.AUTO)
        .text_mode(BigValueTextMode.VALUE)
        .color_mode(BigValueColorMode.BACKGROUND)
        .reduce_options(ReduceDataOptions().values(False).calcs(["lastNotNull"]))
        .with_target(
            PostgresQueryBuilder()
            .query(UNHEALTHY_DEVICES_SQL)
            .datasource(postgres_ref())
            .format("table")
        )
        .thresholds(
            ThresholdsConfig().steps(
                [
                    Threshold(value=0, color="green"),
                    Threshold(value=2, color="yellow"),
                    Threshold(value=4, color="orange"),
                    Threshold(value=6, color="red"),
                ]
            )
        )
    )


def build_heartbeats_by_device_panel() -> timeseries.Panel:
    return (
        timeseries.Panel()
        .title("Heartbeats By Device")
        .id(1)
        .grid_pos(GridPos(h=8, w=24, x=0, y=4))
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
        .grid_pos(GridPos(h=12, w=24, x=0, y=12))
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
        .with_variable(build_device_card_variable())
        .with_panel(build_total_devices_panel())
        .with_panel(build_unhealthy_devices_panel())
        .with_panel(build_heartbeats_by_device_panel())
        .with_panel(build_latest_heartbeat_per_device_panel())
        .with_panel(build_device_health_card_panel())
    )

    return json_from_builder(dash)
