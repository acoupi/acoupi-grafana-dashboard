from __future__ import annotations

from scripts.grafana_dashboards_common import (
    geomap_panel,
    grafana_dashboard,
    json_from_builder,
    set_table_defaults,
    set_targets,
    table_panel,
    target,
    thresholds_red_green,
)


def build_dashboard() -> dict:
    dashboard = grafana_dashboard(
        "Deployments V2",
        "acoupi-deployments-v2",
        ["acoupi", "deployments"],
        refresh="30s",
        time_from="now-30d",
        time_to="now",
        editable=False,
        version=1,
    )
    panels = []

    deployment_map = json_from_builder(geomap_panel("Deployment Map", 1, 16, 24, 0, 0))
    deployment_map["fieldConfig"] = {
        "defaults": {
            "color": {"mode": "thresholds"},
            "mappings": [],
            "thresholds": json_from_builder(thresholds_red_green()),
        },
        "overrides": [],
    }
    deployment_map["options"] = {
        "basemap": {"config": {}, "name": "Layer 0", "type": "default"},
        "controls": {
            "mouseWheelZoom": True,
            "showAttribution": True,
            "showDebug": False,
            "showMeasure": False,
            "showScale": True,
            "showZoom": True,
        },
        "layers": [
            {
                "config": {
                    "showLegend": False,
                    "style": {
                        "color": {"field": "healthy_last_6h", "fixed": "dark-green"},
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
                },
                "location": {
                    "mode": "coords",
                    "latitude": "latitude",
                    "longitude": "longitude",
                },
                "name": "Deployments",
                "type": "markers",
            }
        ],
        "view": {"allLayers": True, "id": "fit", "lat": 0, "lon": 0, "zoom": 1},
    }
    set_targets(
        deployment_map,
        target(
            "table",
            "WITH latest_deployments AS (\n  SELECT DISTINCT ON (devices.device_name)\n    deployments.id,\n    deployments.deployment_uuid,\n    deployments.name,\n    deployments.latitude,\n    deployments.longitude,\n    deployments.started_on,\n    deployments.ended_on,\n    devices.device_name,\n    devices.serial_number\n  FROM deployments\n  JOIN devices ON devices.id = deployments.device_id\n  WHERE deployments.latitude IS NOT NULL\n    AND deployments.longitude IS NOT NULL\n  ORDER BY devices.device_name, deployments.started_on DESC\n), heartbeat_status AS (\n  SELECT\n    mqtt_messages.device_id AS device_name,\n    MAX(mqtt_messages.received_at) FILTER (WHERE mqtt_messages.message_type = 'heartbeat') AS last_heartbeat_at\n  FROM mqtt_messages\n  GROUP BY mqtt_messages.device_id\n), recording_counts AS (\n  SELECT\n    recordings.deployment_id,\n    COUNT(*) AS recordings_count\n  FROM recordings\n  GROUP BY recordings.deployment_id\n)\nSELECT\n  latest_deployments.device_name,\n  latest_deployments.serial_number,\n  latest_deployments.name AS deployment_name,\n  latest_deployments.latitude,\n  latest_deployments.longitude,\n  latest_deployments.started_on,\n  latest_deployments.ended_on,\n  heartbeat_status.last_heartbeat_at,\n  CASE\n    WHEN heartbeat_status.last_heartbeat_at >= NOW() - INTERVAL '6 hours' THEN 1\n    ELSE 0\n  END AS healthy_last_6h,\n  COALESCE(recording_counts.recordings_count, 0) AS recordings_count\nFROM latest_deployments\nLEFT JOIN heartbeat_status ON heartbeat_status.device_name = latest_deployments.device_name\nLEFT JOIN recording_counts ON recording_counts.deployment_id = latest_deployments.id\nORDER BY latest_deployments.device_name;",
        ),
    )
    panels.append(deployment_map)

    deployment_table = json_from_builder(
        table_panel("Deployment Table", 2, 14, 24, 0, 16)
    )
    set_table_defaults(deployment_table)
    set_targets(
        deployment_table,
        target(
            "table",
            "WITH heartbeat_status AS (\n  SELECT\n    mqtt_messages.device_id AS device_name,\n    MAX(mqtt_messages.received_at) FILTER (WHERE mqtt_messages.message_type = 'heartbeat') AS last_heartbeat_at\n  FROM mqtt_messages\n  GROUP BY mqtt_messages.device_id\n), recording_counts AS (\n  SELECT\n    recordings.deployment_id,\n    COUNT(*) AS recordings_count\n  FROM recordings\n  GROUP BY recordings.deployment_id\n)\nSELECT\n  deployments.deployment_uuid,\n  devices.device_name,\n  devices.serial_number,\n  deployments.name AS deployment_name,\n  deployments.latitude,\n  deployments.longitude,\n  deployments.started_on,\n  deployments.ended_on,\n  heartbeat_status.last_heartbeat_at,\n  CASE\n    WHEN heartbeat_status.last_heartbeat_at >= NOW() - INTERVAL '6 hours' THEN true\n    ELSE false\n  END AS healthy_last_6h,\n  COALESCE(recording_counts.recordings_count, 0) AS recordings_count\nFROM deployments\nJOIN devices ON devices.id = deployments.device_id\nLEFT JOIN heartbeat_status ON heartbeat_status.device_name = devices.device_name\nLEFT JOIN recording_counts ON recording_counts.deployment_id = deployments.id\nORDER BY deployments.started_on DESC;",
        ),
    )
    panels.append(deployment_table)

    dashboard["panels"] = panels
    return dashboard
