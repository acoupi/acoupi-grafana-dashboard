from __future__ import annotations

from pathlib import Path
from typing import Any

from grafana_foundation_sdk.builders.common import VizLegendOptions, VizTooltipOptions
from grafana_foundation_sdk.builders.dashboard import FieldColor, ThresholdsConfig
from grafana_foundation_sdk.cog.encoder import JSONEncoder
from grafana_foundation_sdk.models.common import (
    LegendDisplayMode,
    LegendPlacement,
    SortOrder,
    TooltipDisplayMode,
)
from grafana_foundation_sdk.models.dashboard import (
    DataSourceRef,
    FieldColorModeId,
    Threshold,
    ThresholdsMode,
)

POSTGRES_DATASOURCE_UID = "acoupi-postgres"


def json_from_builder(builder: Any) -> dict[str, Any]:
    import json

    return json.loads(json.dumps(builder.build(), cls=JSONEncoder))


def postgres_ref() -> DataSourceRef:
    return DataSourceRef(type_val="postgres", uid=POSTGRES_DATASOURCE_UID)


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
    return FieldColor().mode(FieldColorModeId.PALETTE_CLASSIC)


def thresholds_red_green() -> Any:
    return (
        ThresholdsConfig()
        .mode(ThresholdsMode.ABSOLUTE)
        .steps([Threshold(color="red"), Threshold(value=1, color="green")])
    )


def write_dashboard(output_path: Path, dashboard: dict[str, Any]) -> None:
    import json

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(dashboard, indent=2) + "\n", encoding="utf-8")
