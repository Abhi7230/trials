"""Replay simulator for comparing routing policies."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from modelgate.catalog import Catalog
from modelgate.policies import Policy, get_policy


@dataclass
class TraceRequest:
    """Trace request from JSONL."""

    prompt_length: int
    completion_length: int
    capabilities: frozenset[str]


@dataclass
class PolicyResult:
    """Simulation result for one policy."""

    policy_name: str
    total_cost: float
    total_requests: int
    p50_latency: float
    p95_latency: float
    failed_requests: int
    fallback_count: int


class Simulator:
    """Replay trace against policies."""

    def __init__(self, catalog: Catalog):
        self.catalog = catalog

    def load_trace(self, path: Path) -> list[TraceRequest]:
        """Load trace from JSONL file."""
        requests = []
        with path.open() as f:
            for line in f:
                data = json.loads(line)
                requests.append(
                    TraceRequest(
                        prompt_length=data["prompt_length"],
                        completion_length=data["completion_length"],
                        capabilities=frozenset(data.get("capabilities", [])),
                    )
                )
        return requests

    def simulate_policy(self, policy: Policy, trace: list[TraceRequest]) -> PolicyResult:
        """Simulate a policy against a trace."""
        total_cost = 0.0
        latencies: list[float] = []
        failed = 0
        fallback = 0

        for req in trace:
            # Filter candidates
            min_context = req.prompt_length + req.completion_length
            candidates = self.catalog.filter(
                min_context=min_context,
                required_capabilities=req.capabilities,
            )

            if not candidates:
                failed += 1
                continue

            # Rank by policy
            ranked = policy.rank(candidates, req.prompt_length, req.completion_length)

            if not ranked:
                failed += 1
                continue

            # Use first (best) candidate
            model, _score = ranked[0]

            # Calculate cost
            cost = model.blended_cost(req.prompt_length, req.completion_length)
            total_cost += cost

            # Record latency
            latencies.append(model.avg_latency_ms)

            # Fallback simulation (simplified: 5% chance)
            # In real execution, this would come from actual failures
            if len(ranked) > 1 and (hash(str(req)) % 20 == 0):
                fallback += 1

        # Calculate percentiles
        sorted_latencies = sorted(latencies)
        p50 = sorted_latencies[len(sorted_latencies) // 2] if sorted_latencies else 0.0
        p95_idx = int(len(sorted_latencies) * 0.95)
        p95 = sorted_latencies[p95_idx] if sorted_latencies else 0.0

        return PolicyResult(
            policy_name="",  # Will be set by caller
            total_cost=total_cost,
            total_requests=len(trace),
            p50_latency=p50,
            p95_latency=p95,
            failed_requests=failed,
            fallback_count=fallback,
        )

    def compare_policies(
        self, policy_names: list[str], trace: list[TraceRequest]
    ) -> list[PolicyResult]:
        """Compare multiple policies on a trace."""
        results = []

        for name in policy_names:
            policy = get_policy(name)
            result = self.simulate_policy(policy, trace)
            result.policy_name = name
            results.append(result)

        return results


def format_results_table(results: list[PolicyResult]) -> str:
    """Format results as a text table."""
    lines = []
    lines.append("=" * 100)
    lines.append("SIMULATION RESULTS")
    lines.append("=" * 100)
    lines.append("")

    # Header
    lines.append(
        f"{'Policy':<20} {'Cost ($)':<12} {'P50 (ms)':<10} "
        f"{'P95 (ms)':<10} {'Failures':<10} {'Fallbacks':<10}"
    )
    lines.append("-" * 100)

    # Rows
    for r in results:
        lines.append(
            f"{r.policy_name:<20} ${r.total_cost:<11.6f} "
            f"{r.p50_latency:<10.0f} {r.p95_latency:<10.0f} "
            f"{r.failed_requests:<10} {r.fallback_count:<10}"
        )

    lines.append("=" * 100)

    # Savings calculation
    if len(results) >= 2:
        baseline = max(results, key=lambda r: r.total_cost)
        for r in results:
            if r.policy_name != baseline.policy_name:
                savings = baseline.total_cost - r.total_cost
                pct = (savings / baseline.total_cost * 100) if baseline.total_cost > 0 else 0
                lines.append(
                    f"💰 {r.policy_name} saves ${savings:.6f} ({pct:.1f}%) vs {baseline.policy_name}"
                )

    return "\n".join(lines)


def format_results_json(results: list[PolicyResult]) -> str:
    """Format results as JSON."""
    data: list[dict[str, Any]] = []
    for r in results:
        data.append(
            {
                "policy": r.policy_name,
                "total_cost_usd": r.total_cost,
                "total_requests": r.total_requests,
                "p50_latency_ms": r.p50_latency,
                "p95_latency_ms": r.p95_latency,
                "failed_requests": r.failed_requests,
                "fallback_count": r.fallback_count,
            }
        )
    return json.dumps({"results": data}, indent=2)
