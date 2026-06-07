from __future__ import annotations

from pathlib import Path

from .dashboard_deployments import build_dashboard as build_deployments_dashboard
from .dashboard_health import build_dashboard as build_health_dashboard
from .dashboard_messages import build_dashboard as build_messages_dashboard
from .dashboard_observations import build_dashboard as build_observations_dashboard
from .dashboard_recordings import build_dashboard as build_recordings_dashboard
from .dashboards_common import write_dashboard

ROOT = Path(__file__).parent.parent
OUTPUT_DIR = ROOT / "dashboards"


def main() -> None:
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
