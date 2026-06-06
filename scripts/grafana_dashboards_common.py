from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from grafana_foundation_sdk.builders import (
    barchart,
    geomap,
    statetimeline,
    table,
    timeseries,
)
from grafana_foundation_sdk.builders.common import VizLegendOptions, VizTooltipOptions
from grafana_foundation_sdk.builders.dashboard import (
    AnnotationQuery,
    CustomVariable,
    Dashboard,
    FieldColor as FieldColorBuilder,
    QueryVariable,
    ThresholdsConfig as ThresholdsConfigBuilder,
)
from grafana_foundation_sdk.cog.encoder import JSONEncoder
from grafana_foundation_sdk.models import dashboard as dashboard_models
from grafana_foundation_sdk.models.common import (
    GraphDrawStyle,
    LegendDisplayMode,
    LegendPlacement,
    LineInterpolation,
    SortOrder,
    TableCellHeight,
    TimeZoneBrowser,
    TooltipDisplayMode,
    VisibilityMode,
)
from grafana_foundation_sdk.models.dashboard import (
    DashboardCursorSync,
    DataSourceRef,
    GridPos,
    Threshold,
    VariableHide,
    VariableOption,
    VariableRefresh,
    VariableSort,
)

POSTGRES_DATASOURCE_UID = "acoupi-postgres"
POSTGRES_DATASOURCE = {"type": "postgres", "uid": POSTGRES_DATASOURCE_UID}
SCHEMA_VERSION = 39


def grafana_dashboard(
    title: str,
    uid: str,
    tags: list[str],
    *,
    refresh: str,
    time_from: str,
    time_to: str,
    editable: bool = True,
    version: int = 1,
) -> dict[str, Any]:
    dashboard = (
        Dashboard(title)
        .uid(uid)
        .tags(tags)
        .refresh(refresh)
        .style("dark")
        .timezone(TimeZoneBrowser)
        .time(time_from, time_to)
        .tooltip(DashboardCursorSync.OFF)
        .editable()
        .version(version)
        .annotation(
            AnnotationQuery()
            .datasource(DataSourceRef(type_val="grafana", uid="-- Grafana --"))
            .enable(True)
            .hide(True)
            .icon_color("rgba(0, 211, 255, 1)")
            .name("Annotations & Alerts")
            .type("dashboard")
        )
    )
    payload = json_from_builder(dashboard)
    payload["editable"] = editable
    payload["schemaVersion"] = SCHEMA_VERSION
    payload["id"] = None
    payload["links"] = []
    payload["timepicker"] = {}
    payload["weekStart"] = ""
    payload["fiscalYearStartMonth"] = 0
    payload["graphTooltip"] = 0
    payload.setdefault("templating", {})
    payload["templating"].setdefault("list", [])
    return payload


def json_from_builder(builder: Any) -> dict[str, Any]:
    import json

    return json.loads(json.dumps(builder.build(), cls=JSONEncoder))


def postgres_ref() -> DataSourceRef:
    return DataSourceRef(type_val="postgres", uid=POSTGRES_DATASOURCE_UID)


def grid(h: int, w: int, x: int, y: int) -> GridPos:
    return GridPos(h=h, w=w, x=x, y=y)


def default_legend(display_mode: str = "list") -> VizLegendOptions:
    legend_mode = (
        LegendDisplayMode.LIST if display_mode == "list" else LegendDisplayMode.TABLE
    )
    return (
        VizLegendOptions()
        .calcs([])
        .display_mode(legend_mode)
        .placement(LegendPlacement.BOTTOM)
        .show_legend(True)
    )


def single_tooltip() -> VizTooltipOptions:
    return VizTooltipOptions().mode(TooltipDisplayMode.SINGLE).sort(SortOrder.NONE)


def multi_tooltip_desc() -> VizTooltipOptions:
    return VizTooltipOptions().mode(TooltipDisplayMode.MULTI).sort(SortOrder.DESCENDING)


def classic_palette() -> Any:
    return FieldColorBuilder().mode(dashboard_models.FieldColorModeId.PALETTE_CLASSIC)


def thresholds_red_green() -> Any:
    return (
        ThresholdsConfigBuilder()
        .mode(dashboard_models.ThresholdsMode.ABSOLUTE)
        .steps([Threshold(color="red"), Threshold(value=1, color="green")])
    )


def timeseries_panel(
    title: str,
    panel_id: int,
    h: int,
    w: int,
    x: int,
    y: int,
    *,
    legend_mode: str = "list",
) -> timeseries.Panel:
    return (
        timeseries.Panel()
        .title(title)
        .id(panel_id)
        .grid_pos(grid(h, w, x, y))
        .datasource(postgres_ref())
        .color_scheme(classic_palette())
        .legend(default_legend(legend_mode))
        .tooltip(single_tooltip())
    )


def point_timeseries_panel(
    title: str, panel_id: int, h: int, w: int, x: int, y: int
) -> timeseries.Panel:
    return (
        timeseries_panel(title, panel_id, h, w, x, y)
        .draw_style(GraphDrawStyle.POINTS)
        .line_interpolation(LineInterpolation.LINEAR)
        .line_width(0)
        .point_size(8)
        .show_points(VisibilityMode.ALWAYS)
        .span_nulls(False)
        .min(0)
    )


def barchart_panel(
    title: str, panel_id: int, h: int, w: int, x: int, y: int
) -> barchart.Panel:
    return (
        barchart.Panel()
        .title(title)
        .id(panel_id)
        .grid_pos(grid(h, w, x, y))
        .datasource(postgres_ref())
        .color_scheme(classic_palette())
        .legend(default_legend("table"))
        .tooltip(multi_tooltip_desc())
    )


def table_panel(
    title: str, panel_id: int, h: int, w: int, x: int, y: int
) -> table.Panel:
    return (
        table.Panel()
        .title(title)
        .id(panel_id)
        .grid_pos(grid(h, w, x, y))
        .datasource(postgres_ref())
        .show_header(True)
        .cell_height(TableCellHeight.SM)
    )


def geomap_panel(
    title: str, panel_id: int, h: int, w: int, x: int, y: int
) -> geomap.Panel:
    return (
        geomap.Panel()
        .title(title)
        .id(panel_id)
        .grid_pos(grid(h, w, x, y))
        .datasource(postgres_ref())
    )


def state_timeline_panel(
    title: str, panel_id: int, h: int, w: int, x: int, y: int
) -> statetimeline.Panel:
    return (
        statetimeline.Panel()
        .title(title)
        .id(panel_id)
        .grid_pos(grid(h, w, x, y))
        .datasource(postgres_ref())
    )


def confidence_threshold_variable() -> dict[str, Any]:
    return {
        "current": {"selected": True, "text": "0.7", "value": "0.7"},
        "hide": 0,
        "includeAll": False,
        "label": "Confidence Threshold",
        "multi": False,
        "name": "confidence_threshold",
        "options": [
            {"selected": False, "text": "0.5", "value": "0.5"},
            {"selected": True, "text": "0.7", "value": "0.7"},
            {"selected": False, "text": "0.9", "value": "0.9"},
        ],
        "query": "0.5,0.7,0.9",
        "type": "custom",
    }


def query_variable(
    name: str,
    label: str,
    query: str,
    *,
    current_text: str,
    current_value: str,
    sort: VariableSort,
) -> dict[str, Any]:
    variable = json_from_builder(
        QueryVariable(name)
        .label(label)
        .datasource(postgres_ref())
        .hide(VariableHide.DONT_HIDE)
        .include_all(False)
        .multi(False)
        .current(VariableOption(selected=True, text=current_text, value=current_value))
        .query(query)
        .refresh(VariableRefresh.ON_DASHBOARD_LOAD)
        .sort(sort)
        .options([])
    )
    variable.pop("id", None)
    variable.pop("skipUrlSync", None)
    variable.pop("auto", None)
    variable.pop("auto_min", None)
    variable.pop("auto_count", None)
    variable["definition"] = query
    return variable


def target(format_type: str, sql: str, *, ref_id: str = "A") -> dict[str, Any]:
    return {
        "datasource": deepcopy(POSTGRES_DATASOURCE),
        "format": format_type,
        "rawQuery": True,
        "rawSql": sql,
        "refId": ref_id,
    }


def set_targets(panel: dict[str, Any], *targets: dict[str, Any]) -> dict[str, Any]:
    panel["targets"] = list(targets)
    return panel


def set_table_defaults(panel: dict[str, Any]) -> dict[str, Any]:
    panel["fieldConfig"] = {"defaults": {}, "overrides": []}
    panel["options"] = {
        "cellHeight": "sm",
        "footer": {"countRows": False, "fields": "", "reducer": ["sum"], "show": False},
        "showHeader": True,
    }
    return panel


def write_dashboard(output_path: Path, dashboard: dict[str, Any]) -> None:
    import json

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(dashboard, indent=2) + "\n", encoding="utf-8")
