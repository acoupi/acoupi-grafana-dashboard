from __future__ import annotations

from grafana_foundation_sdk.models.dashboard import VariableSort

from scripts.grafana_dashboards_common import (
    barchart_panel,
    confidence_threshold_variable,
    grafana_dashboard,
    json_from_builder,
    multi_tooltip_desc,
    query_variable,
    set_table_defaults,
    set_targets,
    table_panel,
    target,
    timeseries_panel,
)


def build_dashboard() -> dict:
    dashboard = grafana_dashboard(
        "Observations V2",
        "acoupi-observations-v2",
        ["acoupi", "ecology"],
        refresh="30s",
        time_from="now-30d",
        time_to="now",
        version=1,
    )
    dashboard["templating"]["list"] = [
        confidence_threshold_variable(),
        query_variable(
            "device_name",
            "Device",
            "SELECT '__all' AS __value, 'All' AS __text UNION ALL SELECT device_name AS __value, device_name AS __text FROM devices ORDER BY __text;",
            current_text="All",
            current_value="__all",
            sort=VariableSort.ALPHABETICAL_ASC,
        ),
        query_variable(
            "recording_day",
            "Recording Day (Hourly Panel)",
            "SELECT DISTINCT to_char(recorded_on::date, 'YYYY-MM-DD') AS recording_day FROM observations ORDER BY recording_day DESC;",
            current_text="",
            current_value="",
            sort=VariableSort.NUMERICAL_ASC,
        ),
    ]
    panels = []

    per_day = json_from_builder(
        timeseries_panel(
            "Observations Per Species Per Day (>= ${confidence_threshold})",
            3,
            10,
            24,
            0,
            0,
            legend_mode="table",
        )
    )
    per_day["options"]["tooltip"] = json_from_builder(multi_tooltip_desc())
    set_targets(
        per_day,
        target(
            "time_series",
            "SELECT\n  date_trunc('day', o.recorded_on) AS time,\n  ot.tag_value AS metric,\n  COUNT(*)::double precision AS value\nFROM observations o\nJOIN observation_tags ot ON ot.observation_id = o.id\nJOIN devices ON devices.id = o.device_id\nWHERE ot.tag_key = 'species'\n  AND COALESCE(ot.confidence_score, 0) >= ${confidence_threshold}\n  AND ('${device_name}' = '__all' OR devices.device_name = '${device_name}')\n  AND o.recorded_on >= $__timeFrom()\n  AND o.recorded_on <= $__timeTo()\nGROUP BY 1, 2\nORDER BY 1, 2;",
        ),
    )
    panels.append(per_day)

    per_hour = json_from_builder(
        barchart_panel(
            "Observations Per Hour Of Day By Species (>= ${confidence_threshold})",
            4,
            10,
            24,
            0,
            10,
        )
    )
    per_hour["timeFrom"] = "1d"
    set_targets(
        per_hour,
        target(
            "time_series",
            "SELECT\n  date_trunc('day', to_timestamp(0)) + make_interval(hours => EXTRACT(hour FROM o.recorded_on)::int) AS time,\n  ot.tag_value AS metric,\n  COUNT(*)::double precision AS value\nFROM observations o\nJOIN observation_tags ot ON ot.observation_id = o.id\nJOIN devices ON devices.id = o.device_id\nWHERE ot.tag_key = 'species'\n  AND COALESCE(ot.confidence_score, 0) >= ${confidence_threshold}\n  AND ('${device_name}' = '__all' OR devices.device_name = '${device_name}')\n  AND o.recorded_on::date = '${recording_day}'::date\nGROUP BY 1, 2\nORDER BY 1, 2;",
        ),
    )
    panels.append(per_hour)

    matrix = json_from_builder(
        table_panel(
            "Observations Per Species Per Hour Matrix (>= ${confidence_threshold})",
            5,
            12,
            24,
            0,
            20,
        )
    )
    set_table_defaults(matrix)
    matrix["transformations"] = [
        {
            "id": "groupingToMatrix",
            "options": {
                "columnField": "hour_of_day",
                "emptyValue": "0",
                "rowField": "species",
                "valueField": "detections",
            },
        }
    ]
    set_targets(
        matrix,
        target(
            "table",
            "SELECT\n  ot.tag_value AS species,\n  EXTRACT(hour FROM o.recorded_on)::int AS hour_of_day,\n  COUNT(*)::double precision AS detections\nFROM observations o\nJOIN observation_tags ot ON ot.observation_id = o.id\nJOIN devices ON devices.id = o.device_id\nWHERE ot.tag_key = 'species'\n  AND COALESCE(ot.confidence_score, 0) >= ${confidence_threshold}\n  AND ('${device_name}' = '__all' OR devices.device_name = '${device_name}')\n  AND o.recorded_on >= $__timeFrom()\n  AND o.recorded_on <= $__timeTo()\nGROUP BY 1, 2\nORDER BY 1, 2;",
        ),
    )
    panels.append(matrix)

    records = json_from_builder(
        table_panel(
            "Observation Records (>= ${confidence_threshold})", 6, 14, 24, 0, 32
        )
    )
    set_table_defaults(records)
    set_targets(
        records,
        target(
            "table",
            "SELECT\n  species_tags.tag_value AS species,\n  devices.device_name AS device,\n  observations.recorded_on,\n  COALESCE(species_tags.confidence_score, 0) AS confidence_score,\n  observations.classified_by AS model_name,\n  observations.detection_score,\n  observations.event_start_seconds,\n  observations.event_end_seconds,\n  observations.frequency_low_hz,\n  observations.frequency_high_hz\nFROM observations\nJOIN observation_tags AS species_tags ON species_tags.observation_id = observations.id\nJOIN devices ON devices.id = observations.device_id\nWHERE species_tags.tag_key = 'species'\n  AND COALESCE(species_tags.confidence_score, 0) >= ${confidence_threshold}\n  AND ('${device_name}' = '__all' OR devices.device_name = '${device_name}')\n  AND observations.recorded_on >= $__timeFrom()\n  AND observations.recorded_on <= $__timeTo()\nORDER BY observations.recorded_on DESC\nLIMIT 500;",
        ),
    )
    panels.append(records)

    dashboard["panels"] = panels
    return dashboard
