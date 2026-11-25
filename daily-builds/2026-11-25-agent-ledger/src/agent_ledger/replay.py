"""Scenario replay engine."""

import json
import tempfile
from pathlib import Path
from typing import Any

import yaml
from fastapi.testclient import TestClient
from rich.console import Console
from rich.table import Table

from agent_ledger.app import create_app
from agent_ledger.clock import FixedClock


class ScenarioReplay:
    """Replays API scenarios for testing."""

    def __init__(self, db_path: str = ":memory:", clock: FixedClock | None = None):
        self.clock = clock or FixedClock()
        self.app = create_app(db_path=db_path, clock=self.clock)
        self.client = TestClient(self.app)

    def load_scenario(self, path: str) -> dict[str, Any]:
        """Load scenario from YAML or JSONL file."""
        file_path = Path(path)
        
        if file_path.suffix in [".yaml", ".yml"]:
            with open(file_path) as f:
                return yaml.safe_load(f)
        elif file_path.suffix == ".jsonl":
            steps = []
            with open(file_path) as f:
                for line in f:
                    if line.strip():
                        steps.append(json.loads(line))
            return {"steps": steps}
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

    def replay(self, scenario: dict[str, Any], format: str = "text") -> dict[str, Any]:
        """Replay a scenario."""
        steps = scenario.get("steps", [])
        results = []
        failures = []

        for i, step in enumerate(steps):
            method = step.get("method", "POST").upper()
            path = step["path"]
            data = step.get("data", {})
            headers = step.get("headers", {})
            expect = step.get("expect", {})
            advance = step.get("advance")

            # Advance clock if requested
            if advance:
                self.clock.advance(**advance)

            # Make request
            try:
                if method == "GET":
                    response = self.client.get(path, headers=headers)
                elif method == "POST":
                    response = self.client.post(path, json=data, headers=headers)
                elif method == "PUT":
                    response = self.client.put(path, json=data, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                result = {
                    "step": i + 1,
                    "method": method,
                    "path": path,
                    "status": response.status_code,
                    "response": response.json() if response.text else {},
                }

                # Check expectations
                if expect:
                    if "status" in expect and response.status_code != expect["status"]:
                        failures.append({
                            "step": i + 1,
                            "expected_status": expect["status"],
                            "actual_status": response.status_code,
                        })

                results.append(result)

            except Exception as e:
                result = {
                    "step": i + 1,
                    "method": method,
                    "path": path,
                    "error": str(e),
                }
                results.append(result)
                failures.append({"step": i + 1, "error": str(e)})

        # Check invariants
        invariants_response = self.client.get("/v1/admin/invariants")
        invariants = invariants_response.json()

        return {
            "results": results,
            "failures": failures,
            "invariants": invariants,
            "ok": len(failures) == 0 and invariants.get("ok", False),
        }

    def print_results(self, replay_result: dict[str, Any], format: str = "text") -> None:
        """Print replay results."""
        if format == "json":
            print(json.dumps(replay_result, indent=2))
            return

        console = Console()

        # Print results table
        table = Table(title="Scenario Replay Results")
        table.add_column("Step", style="cyan")
        table.add_column("Method", style="yellow")
        table.add_column("Path", style="green")
        table.add_column("Status", style="blue")

        for result in replay_result["results"]:
            table.add_row(
                str(result["step"]),
                result.get("method", ""),
                result.get("path", ""),
                str(result.get("status", result.get("error", ""))),
            )

        console.print(table)

        # Print failures
        if replay_result["failures"]:
            console.print("\n[red]Failures:[/red]")
            for failure in replay_result["failures"]:
                console.print(f"  Step {failure['step']}: {failure}")

        # Print invariants
        invariants = replay_result["invariants"]
        if invariants.get("ok"):
            console.print("\n[green]✓ All invariants passed[/green]")
        else:
            console.print("\n[red]✗ Invariant violations:[/red]")
            for violation in invariants.get("violations", []):
                console.print(f"  {violation['type']}: {violation['description']}")

        # Print overall status
        if replay_result["ok"]:
            console.print("\n[green]✓ Scenario passed[/green]")
        else:
            console.print("\n[red]✗ Scenario failed[/red]")


def replay_file(path: str, db_path: str = ":memory:", format: str = "text") -> int:
    """Replay a scenario file. Returns exit code."""
    replayer = ScenarioReplay(db_path=db_path)
    scenario = replayer.load_scenario(path)
    result = replayer.replay(scenario, format=format)
    replayer.print_results(result, format=format)
    return 0 if result["ok"] else 1
