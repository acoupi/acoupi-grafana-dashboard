from __future__ import annotations

from pathlib import Path

from grafana_foundation_sdk.cog.plugins import register_default_plugins
from grafana_foundation_sdk.cog.runtime import register_dataquery_variant

from scripts.grafana_dashboard_deployments import (
    build_dashboard as build_deployments_dashboard,
)
from scripts.grafana_dashboard_health import build_dashboard as build_health_dashboard
from scripts.grafana_dashboard_messages import (
    build_dashboard as build_messages_dashboard,
)
from scripts.grafana_dashboard_observations import (
    build_dashboard as build_observations_dashboard,
)
from scripts.grafana_dashboard_recordings import (
    build_dashboard as build_recordings_dashboard,
)
from scripts.grafana_dashboards_common import write_dashboard
from scripts.grafana_sql_datasource import postgres_query_variant_config

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "infra" / "grafana" / "dashboards"


def main() -> None:
    register_default_plugins()
    register_dataquery_variant(postgres_query_variant_config())

    dashboards = {
        OUTPUT_DIR / "acoupi-messages.json": build_messages_dashboard(),
        OUTPUT_DIR / "acoupi-health.json": build_health_dashboard(),
        OUTPUT_DIR / "acoupi-observations.json": build_observations_dashboard(),
        OUTPUT_DIR / "acoupi-deployments.json": build_deployments_dashboard(),
        OUTPUT_DIR / "acoupi-recordings.json": build_recordings_dashboard(),
    }

    for output_path, dashboard in dashboards.items():
        write_dashboard(output_path, dashboard)


if __name__ == "__main__":
    main()
