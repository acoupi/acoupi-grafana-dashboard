from __future__ import annotations

from grafana_foundation_sdk.builders import (
    bargauge,
    dashboard,
    heatmap,
    statushistory,
    table,
)
from grafana_foundation_sdk.builders.common import ReduceDataOptions
from grafana_foundation_sdk.builders.dashboard import FieldColor
from grafana_foundation_sdk.builders.heatmap import HeatmapColorOptions, YAxisConfig
from grafana_foundation_sdk.models.common import (
    BarGaugeDisplayMode,
    BarGaugeValueMode,
    TableCellHeight,
    TimeZoneBrowser,
    VizOrientation,
)
from grafana_foundation_sdk.models.dashboard import (
    DashboardCursorSync,
    FieldColorModeId,
    GridPos,
    VariableHide,
    VariableOption,
    VariableRefresh,
    VariableSort,
)

from scripts.grafana_dashboards_common import (
    json_from_builder,
    multi_tooltip_desc,
    postgres_ref,
)
from scripts.grafana_sql_datasource import PostgresQueryBuilder

OBSERVATIONS_PER_DAY_SQL = """
SELECT
  date_trunc('day', o.recorded_on) AS time,
  ot.tag_value AS metric,
  COUNT(*)::double precision AS value
FROM observations o
JOIN observation_tags ot ON ot.observation_id = o.id
JOIN devices ON devices.id = o.device_id
WHERE ot.tag_key = '${tag_key}'
  AND COALESCE(ot.confidence_score, 0) >= ${confidence_threshold}
  AND ('${device_name}' = '__all' OR devices.device_name = '${device_name}')
  AND ('__all' in (${tag_value}) OR ot.tag_value IN (${tag_value}))
  AND o.recorded_on >= $__timeFrom()
  AND o.recorded_on <= $__timeTo()
GROUP BY 1, 2
ORDER BY 1, 2;
"""


def build_observations_per_day():
    return (
        statushistory.Panel()
        .title("Observations Per Tag Per Day")
        .description("Shows daily detection counts for the selected tag values.")
        .id(2)
        .grid_pos(GridPos(h=10, w=24, x=0, y=0))
        .datasource(postgres_ref())
        .color_scheme(FieldColor().mode(FieldColorModeId.CONTINUOUS_BL_YL_RD))
        .tooltip(multi_tooltip_desc())
        .with_target(
            PostgresQueryBuilder()
            .query(OBSERVATIONS_PER_DAY_SQL)
            .datasource(postgres_ref())
            .format("time_series")
        )
    )


OBSERVATIONS_PER_HOUR_SQL = """
SELECT
  date_trunc('hour', o.recorded_on) AS time,
  ot.tag_value AS metric,
  COUNT(*)::double precision AS value
FROM observations o
JOIN observation_tags ot ON ot.observation_id = o.id
JOIN devices ON devices.id = o.device_id
WHERE ot.tag_key = '${tag_key}'
  AND COALESCE(ot.confidence_score, 0) >= ${confidence_threshold}
  AND ('${device_name}' = '__all' OR devices.device_name = '${device_name}')
  AND ('__all' in (${tag_value}) OR ot.tag_value IN (${tag_value}))
  AND o.recorded_on >= $__timeFrom()
  AND o.recorded_on <= $__timeTo()
GROUP BY 1, 2
ORDER BY 1, 2;
"""


def build_observations_per_hour():
    return (
        statushistory.Panel()
        .title("Observations Per Hour Of Day By Tag")
        .description("Shows hourly detection counts for the selected tag values.")
        .id(3)
        .grid_pos(GridPos(10, 24, 0, 0))
        .datasource(postgres_ref())
        .color_scheme(FieldColor().mode(FieldColorModeId.CONTINUOUS_BL_YL_RD))
        .tooltip(multi_tooltip_desc())
        .with_target(
            PostgresQueryBuilder()
            .query(OBSERVATIONS_PER_HOUR_SQL)
            .datasource(postgres_ref())
            .format("time_series")
        )
    )


OBSERVATION_TABLE_QUERY = """
SELECT
    selected_tags.tag_key,
    selected_tags.tag_value,
    devices.device_name AS device,
    observations.recorded_on,
    COALESCE(selected_tags.confidence_score, 1) AS confidence_score,
    observations.classified_by AS model_name,
    observations.detection_score,
    observations.event_start_seconds,
    observations.event_end_seconds,
    observations.frequency_low_hz,
    observations.frequency_high_hz
FROM observations
JOIN observation_tags AS selected_tags ON selected_tags.observation_id = observations.id
JOIN devices ON devices.id = observations.device_id
WHERE selected_tags.tag_key = '${tag_key}'
    AND COALESCE(selected_tags.confidence_score, 0) >= ${confidence_threshold}
    AND ('${device_name}' = '__all' OR devices.device_name = '${device_name}')
    AND ('__all' in (${tag_value}) OR selected_tags.tag_value IN (${tag_value}))
    AND observations.recorded_on >= $__timeFrom()
    AND observations.recorded_on <= $__timeTo()
ORDER BY observations.recorded_on DESC
LIMIT 500;
"""


DETECTIONS_PER_TAG_SQL = """
SELECT
    selected_tags.tag_value AS tag_value,
    COUNT(*)::double precision AS value
FROM observations
JOIN observation_tags AS selected_tags ON selected_tags.observation_id = observations.id
JOIN devices ON devices.id = observations.device_id
WHERE selected_tags.tag_key = '${tag_key}'
    AND COALESCE(selected_tags.confidence_score, 0) >= ${confidence_threshold}
    AND ('${device_name}' = '__all' OR devices.device_name = '${device_name}')
    AND ('__all' in (${tag_value}) OR selected_tags.tag_value IN (${tag_value}))
    AND observations.recorded_on >= $__timeFrom()
    AND observations.recorded_on <= $__timeTo()
GROUP BY selected_tags.tag_value
ORDER BY value DESC, tag_value ASC;
"""


def build_detections_per_species_panel():
    return (
        bargauge.Panel()
        .title("Detections Per Tag Value")
        .description("Ranks selected tag values by total detections in the time range.")
        .id(1)
        .grid_pos(GridPos(12, 24, 0, 0))
        .datasource(postgres_ref())
        .color_scheme(FieldColor().mode(FieldColorModeId.CONTINUOUS_BL_YL_RD))
        .orientation(VizOrientation.HORIZONTAL)
        .show_unfilled(True)
        .value_mode(BarGaugeValueMode.COLOR)
        .reduce_options(ReduceDataOptions().values(True))
        .display_mode(BarGaugeDisplayMode.BASIC)
        .min(0)
        .with_target(
            PostgresQueryBuilder()
            .query(DETECTIONS_PER_TAG_SQL)
            .datasource(postgres_ref())
            .format("table")
        )
    )


OBSERVATION_CONFIDENCE_SCORE_SQL = """
SELECT
    observations.recorded_on,
    selected_tags.confidence_score
FROM observations
JOIN observation_tags AS selected_tags ON selected_tags.observation_id = observations.id
JOIN devices ON devices.id = observations.device_id
WHERE selected_tags.tag_key = '${tag_key}'
    AND COALESCE(selected_tags.confidence_score, 1) >= ${confidence_threshold}
    AND ('${device_name}' = '__all' OR devices.device_name = '${device_name}')
    AND ('__all' in (${tag_value}) OR selected_tags.tag_value IN (${tag_value}))
    AND observations.recorded_on >= $__timeFrom()
    AND observations.recorded_on <= $__timeTo()
ORDER BY recorded_on DESC, confidence_score ASC;
"""


def build_confidence_score_panel():
    return (
        heatmap.Panel()
        .title("Confidence Score Heatmap")
        .description(
            "Shows the distribution of observation confidence scores over time."
        )
        .id(4)
        .grid_pos(GridPos(14, 24, 0, 0))
        .datasource(postgres_ref())
        .calculate(True)
        .color(
            HeatmapColorOptions().scheme(FieldColorModeId.CONTINUOUS_BL_YL_RD).steps(20)
        )
        .show_tooltip()
        .y_axis(YAxisConfig().min(0).max(1))
        .with_target(
            PostgresQueryBuilder()
            .query(OBSERVATION_CONFIDENCE_SCORE_SQL)
            .datasource(postgres_ref())
            .format("table")
        )
    )


def build_observation_table():
    return (
        table.Panel()
        .title("Observation Records")
        .description("Lists recent observation records and their detection metadata.")
        .id(5)
        .grid_pos(GridPos(14, 24, 0, 0))
        .datasource(postgres_ref())
        .show_header(True)
        .cell_height(TableCellHeight.SM)
        .with_target(
            PostgresQueryBuilder()
            .query(OBSERVATION_TABLE_QUERY)
            .datasource(postgres_ref())
            .format("table")
        )
    )


DEVICE_NAME_SQL = """
SELECT
    '__all' AS __value,
    'All' AS __text
UNION ALL SELECT
    device_name AS __value,
    device_name AS __text
FROM devices
ORDER BY __text;
"""


def build_device_name_variable():
    return (
        dashboard.QueryVariable("device_name")
        .id("device_name")
        .label("Device")
        .datasource(postgres_ref())
        .hide(VariableHide.DONT_HIDE)
        .include_all(False)
        .multi(False)
        .current(VariableOption(selected=True, text="All", value="__all"))
        .query(DEVICE_NAME_SQL)
        .refresh(VariableRefresh.ON_DASHBOARD_LOAD)
        .sort(VariableSort.ALPHABETICAL_ASC)
        .options([])
    )


TAG_KEY_SQL = """
SELECT DISTINCT
    ot.tag_key AS __value,
    ot.tag_key AS __text
FROM observation_tags as ot
ORDER BY __text;
"""


def build_tag_key_variable():
    return (
        dashboard.QueryVariable("tag_key")
        .id("tag_key")
        .label("Tag Key")
        .datasource(postgres_ref())
        .hide(VariableHide.DONT_HIDE)
        .include_all(False)
        .multi(False)
        .current(VariableOption(selected=True, text="species", value="species"))
        .query(TAG_KEY_SQL)
        .refresh(VariableRefresh.ON_DASHBOARD_LOAD)
        .sort(VariableSort.ALPHABETICAL_ASC)
        .options([])
    )


TAG_VALUE_SQL = """
SELECT
    '__all' AS __value,
    'All' AS __text
UNION ALL SELECT
    ot.tag_value AS __value,
    ot.tag_value AS __text
FROM observation_tags as ot
WHERE
    ot.tag_key = '${tag_key}'
ORDER BY __text;
"""


def build_tag_value_variable():
    return (
        dashboard.QueryVariable("tag_value")
        .id("tag_value")
        .label("Tag Value")
        .datasource(postgres_ref())
        .hide(VariableHide.DONT_HIDE)
        .include_all(False)
        .multi(True)
        .current(VariableOption(selected=True, text="All", value="__all"))
        .query(TAG_VALUE_SQL)
        .refresh(VariableRefresh.ON_DASHBOARD_LOAD)
        .sort(VariableSort.ALPHABETICAL_ASC)
        .options([])
    )


RECORDING_DAY_SQL = """
SELECT DISTINCT
    to_char(recorded_on::date, 'YYYY-MM-DD') AS recording_day
FROM observations
ORDER BY recording_day DESC;
"""


def build_recording_day_variable():
    return (
        dashboard.QueryVariable("recording_day")
        .id("recording_day")
        .label("Recording Day (Hourly Panel)")
        .datasource(postgres_ref())
        .hide(VariableHide.DONT_HIDE)
        .include_all(False)
        .multi(False)
        .current(VariableOption(selected=True, text="", value=""))
        .query(RECORDING_DAY_SQL)
        .refresh(VariableRefresh.ON_DASHBOARD_LOAD)
        .sort(VariableSort.NUMERICAL_ASC)
        .options([])
    )


def build_confidence_threshold_variable():
    return (
        dashboard.CustomVariable("confidence_threshold")
        .id("confidence_threshold")
        .label("Confidence Threshold")
        .hide(VariableHide.DONT_HIDE)
        .include_all(False)
        .multi(False)
        .current(VariableOption(selected=True, text="0.7", value="0.7"))
        .options(
            [
                VariableOption(selected=False, text="0.5", value="0.5"),
                VariableOption(selected=True, text="0.7", value="0.7"),
                VariableOption(selected=False, text="0.9", value="0.9"),
            ]
        )
    )


def build_dashboard() -> dict:
    dash = (
        dashboard.Dashboard("Observations")
        .uid("acoupi-observations")
        .tags(["acoupi", "observations"])
        .refresh("30s")
        .style("dark")
        .timezone(TimeZoneBrowser)
        .time("now-30d", "now")
        .tooltip(DashboardCursorSync.OFF)
        .editable()
        .version(1)
        .with_variable(build_device_name_variable())
        .with_variable(build_tag_key_variable())
        .with_variable(build_tag_value_variable())
        .with_variable(build_confidence_threshold_variable())
        .with_panel(build_detections_per_species_panel())
        .with_panel(build_observations_per_day())
        .with_panel(build_observations_per_hour())
        .with_panel(build_confidence_score_panel())
        .with_panel(build_observation_table())
    )

    return json_from_builder(dash)
