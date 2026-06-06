from __future__ import annotations

from grafana_foundation_sdk.builders import common, dashboard, geomap, table
from grafana_foundation_sdk.models.common import (
    FrameGeometrySourceMode,
    TableCellHeight,
    TimeZoneBrowser,
)
from grafana_foundation_sdk.models.dashboard import DashboardCursorSync, GridPos

from scripts.grafana_dashboards_common import json_from_builder, postgres_ref
from scripts.grafana_sql_datasource import PostgresQueryBuilder

DEPLOYMENT_MAP_SQL = """
WITH latest_deployments AS (
  SELECT DISTINCT ON (devices.device_name)
    deployments.id,
    deployments.deployment_uuid,
    deployments.name,
    deployments.latitude,
    deployments.longitude,
    deployments.started_on,
    deployments.ended_on,
    devices.device_name,
    devices.serial_number
  FROM deployments
  JOIN devices ON devices.id = deployments.device_id
  WHERE deployments.latitude IS NOT NULL
    AND deployments.longitude IS NOT NULL
  ORDER BY devices.device_name, deployments.started_on DESC
), heartbeat_status AS (
  SELECT
    mqtt_messages.device_id AS device_name,
    MAX(mqtt_messages.received_at) FILTER (WHERE mqtt_messages.message_type = 'heartbeat') AS last_heartbeat_at
  FROM mqtt_messages
  GROUP BY mqtt_messages.device_id
), recording_counts AS (
  SELECT
    recordings.deployment_id,
    COUNT(*) AS recordings_count
  FROM recordings
  GROUP BY recordings.deployment_id
)
SELECT
  latest_deployments.device_name,
  latest_deployments.serial_number,
  latest_deployments.name AS deployment_name,
  latest_deployments.latitude,
  latest_deployments.longitude,
  latest_deployments.started_on,
  latest_deployments.ended_on,
  heartbeat_status.last_heartbeat_at,
  CASE
    WHEN heartbeat_status.last_heartbeat_at >= NOW() - INTERVAL '6 hours' THEN 1
    ELSE 0
  END AS healthy_last_6h,
  COALESCE(recording_counts.recordings_count, 0) AS recordings_count
FROM latest_deployments
LEFT JOIN heartbeat_status ON heartbeat_status.device_name = latest_deployments.device_name
LEFT JOIN recording_counts ON recording_counts.deployment_id = latest_deployments.id
ORDER BY latest_deployments.device_name;
"""


def build_deployment_map_panel():
    return (
        geomap.Panel()
        .title("Deployment Map")
        .id(1)
        .grid_pos(GridPos(h=16, w=24, x=0, y=0))
        .datasource(postgres_ref())
        .with_target(
            PostgresQueryBuilder()
            .query(DEPLOYMENT_MAP_SQL)
            .datasource(postgres_ref())
            .format("table")
        )
        .basemap(common.MapLayerOptions().type("default").name("Layer 0"))
        .controls(
            geomap.ControlsOptions()
            .mouse_wheel_zoom(True)
            .show_attribution(True)
            .show_debug(False)
            .show_measure(True)
            .show_scale(True)
            .show_zoom(True)
        )
        .layers(
            [
                common.MapLayerOptions()
                .name("Deployments")
                .type("markers")
                .config(
                    {
                        "showLegend": False,
                        "style": {
                            "color": {
                                "field": "healthy_last_6h",
                                "fixed": "dark-green",
                            },
                            "fill_opacity": 0.8,
                            "size": {"fixed": 8, "max": 15, "min": 4},
                            "symbol": {
                                "fixed": "img/icons/marker/circle.svg",
                                "mode": "fixed",
                            },
                            "textConfig": {
                                "fontSize": 12,
                                "offsetX": 0,
                                "offsetY": 0,
                                "textAlign": "center",
                                "textBaseline": "middle",
                            },
                        },
                    }
                )
                .location(
                    common.FrameGeometrySource()
                    .mode(FrameGeometrySourceMode.COORDS)
                    .latitude("latitude")
                    .longitude("longitude")
                )
            ]
        )
        .view(geomap.MapViewConfig().all_layers(True).id("fit").lat(0).lon(0).zoom(1))
    )


DEPLOYMENT_TABLE_SQL = """
WITH heartbeat_status AS (
  SELECT
    mqtt_messages.device_id AS device_name,
    MAX(mqtt_messages.received_at) FILTER (WHERE mqtt_messages.message_type = 'heartbeat') AS last_heartbeat_at
  FROM mqtt_messages
  GROUP BY mqtt_messages.device_id
), recording_counts AS (
  SELECT
    recordings.deployment_id,
    COUNT(*) AS recordings_count
  FROM recordings
  GROUP BY recordings.deployment_id
)
SELECT
  deployments.deployment_uuid,
  devices.device_name,
  devices.serial_number,
  deployments.name AS deployment_name,
  deployments.latitude,
  deployments.longitude,
  deployments.started_on,
  deployments.ended_on,
  heartbeat_status.last_heartbeat_at,
  CASE
    WHEN heartbeat_status.last_heartbeat_at >= NOW() - INTERVAL '6 hours' THEN true
    ELSE false
  END AS healthy_last_6h,
  COALESCE(recording_counts.recordings_count, 0) AS recordings_count
FROM deployments
JOIN devices ON devices.id = deployments.device_id
LEFT JOIN heartbeat_status ON heartbeat_status.device_name = devices.device_name
LEFT JOIN recording_counts ON recording_counts.deployment_id = deployments.id
ORDER BY deployments.started_on DESC;
"""


def build_deployment_table_panel() -> table.Panel:
    return (
        table.Panel()
        .title("Deployment Table")
        .id(2)
        .grid_pos(GridPos(h=14, w=24, x=0, y=16))
        .datasource(postgres_ref())
        .show_header(True)
        .cell_height(TableCellHeight.SM)
        .with_target(
            PostgresQueryBuilder()
            .query(DEPLOYMENT_TABLE_SQL)
            .datasource(postgres_ref())
            .format("table")
        )
    )


def build_dashboard() -> dict:
    dash = (
        dashboard.Dashboard("Deployments")
        .uid("acoupi-deployments")
        .tags(["acoupi", "deployments"])
        .refresh("30s")
        .style("dark")
        .timezone(TimeZoneBrowser)
        .time("now-30d", "now")
        .tooltip(DashboardCursorSync.OFF)
        .version(1)
        .with_panel(build_deployment_map_panel())
        .with_panel(build_deployment_table_panel())
    )
    return json_from_builder(dash)
