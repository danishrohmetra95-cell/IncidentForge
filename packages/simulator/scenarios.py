"""Scenario loader — loads scenario definitions and configures Digital Twins."""

import json
import os
from pathlib import Path

from packages.simulator.twin import DigitalTwin


SCENARIOS_DIR = Path(__file__).resolve().parent.parent.parent / "scenarios"


def list_scenarios() -> list[dict]:
    """List all available scenario metadata."""
    scenarios = []
    if not SCENARIOS_DIR.exists():
        return scenarios

    for entry in sorted(SCENARIOS_DIR.iterdir()):
        scenario_file = entry / "scenario.json"
        if scenario_file.exists():
            with open(scenario_file) as f:
                data = json.load(f)
            scenarios.append({
                "id": data["id"],
                "title": data["title"],
                "description": data.get("description", ""),
                "service": data.get("service", ""),
                "severity": data.get("severity", "SEV_2"),
            })
    return scenarios


def load_scenario(scenario_id: str) -> dict:
    """Load a scenario definition by ID."""
    for entry in SCENARIOS_DIR.iterdir():
        scenario_file = entry / "scenario.json"
        if scenario_file.exists():
            with open(scenario_file) as f:
                data = json.load(f)
            if data.get("id") == scenario_id:
                return data

    raise ValueError(f"Scenario '{scenario_id}' not found in {SCENARIOS_DIR}")


def create_twin_from_scenario(scenario_data: dict) -> DigitalTwin:
    """Create and configure a Digital Twin from a scenario definition."""
    twin = DigitalTwin()

    fault = scenario_data.get("fault", {})
    if fault:
        twin.inject_fault(fault)

    return twin
