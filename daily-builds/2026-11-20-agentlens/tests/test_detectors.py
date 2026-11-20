"""Tests for detectors."""

import json
from pathlib import Path

from agentlens.detectors.cost_blowup import CostBlowupDetector
from agentlens.detectors.error_ignored import ErrorIgnoredDetector
from agentlens.detectors.hallucinated_tool import HallucinatedToolDetector
from agentlens.detectors.latency_outlier import LatencyOutlierDetector
from agentlens.detectors.loop import ToolCallLoopDetector
from agentlens.detectors.repeated import RepeatedIdenticalCallsDetector
from agentlens.detectors.retry_storm import RetryStormDetector
from agentlens.detectors.token_blowup import TokenBlowupDetector
from agentlens.models import TraceEvent


def test_loop_detector_four_identical() -> None:
    """Test loop detector with 4 identical calls."""
    events = [
        TraceEvent(
            timestamp="t1",
            type="tool_call",
            role="assistant",
            tool_name="foo",
            tool_args={"x": 1},
        ),
        TraceEvent(timestamp="t2", type="tool_result", role="tool", content="ok"),
        TraceEvent(
            timestamp="t3",
            type="tool_call",
            role="assistant",
            tool_name="foo",
            tool_args={"x": 1},
        ),
        TraceEvent(timestamp="t4", type="tool_result", role="tool", content="ok"),
        TraceEvent(
            timestamp="t5",
            type="tool_call",
            role="assistant",
            tool_name="foo",
            tool_args={"x": 1},
        ),
        TraceEvent(timestamp="t6", type="tool_result", role="tool", content="ok"),
        TraceEvent(
            timestamp="t7",
            type="tool_call",
            role="assistant",
            tool_name="foo",
            tool_args={"x": 1},
        ),
    ]

    detector = ToolCallLoopDetector()
    instances = detector.detect(events)

    assert len(instances) == 1
    assert instances[0].pattern_type == "tool-call-loop"
    assert instances[0].details["count"] == 4


def test_loop_detector_fuzzy_args() -> None:
    """Test loop detector with fuzzy matching."""
    events = [
        TraceEvent(
            timestamp="t1",
            type="tool_call",
            role="assistant",
            tool_name="foo",
            tool_args={"x": 1, "y": "hello"},
        ),
        TraceEvent(
            timestamp="t2",
            type="tool_call",
            role="assistant",
            tool_name="foo",
            tool_args={"x": 1, "y": "helo"},  # 90%+ similar
        ),
        TraceEvent(
            timestamp="t3",
            type="tool_call",
            role="assistant",
            tool_name="foo",
            tool_args={"x": 1, "y": "hello"},
        ),
        TraceEvent(
            timestamp="t4",
            type="tool_call",
            role="assistant",
            tool_name="foo",
            tool_args={"x": 1, "y": "hello"},
        ),
    ]

    detector = ToolCallLoopDetector()
    instances = detector.detect(events)

    assert len(instances) == 1
    assert instances[0].details["count"] == 4


def test_loop_detector_two_or_three_not_detected() -> None:
    """Test that 2-3 calls are not detected."""
    events = [
        TraceEvent(
            timestamp="t1",
            type="tool_call",
            role="assistant",
            tool_name="foo",
            tool_args={"x": 1},
        ),
        TraceEvent(
            timestamp="t2",
            type="tool_call",
            role="assistant",
            tool_name="foo",
            tool_args={"x": 1},
        ),
        TraceEvent(
            timestamp="t3",
            type="tool_call",
            role="assistant",
            tool_name="foo",
            tool_args={"x": 1},
        ),
    ]

    detector = ToolCallLoopDetector()
    instances = detector.detect(events)

    assert len(instances) == 0


def test_loop_detector_alternating_tools_not_detected() -> None:
    """Test that alternating tools don't trigger loop."""
    events = [
        TraceEvent(
            timestamp="t1",
            type="tool_call",
            role="assistant",
            tool_name="foo",
            tool_args={"x": 1},
        ),
        TraceEvent(
            timestamp="t2",
            type="tool_call",
            role="assistant",
            tool_name="bar",
            tool_args={"x": 1},
        ),
        TraceEvent(
            timestamp="t3",
            type="tool_call",
            role="assistant",
            tool_name="foo",
            tool_args={"x": 1},
        ),
        TraceEvent(
            timestamp="t4",
            type="tool_call",
            role="assistant",
            tool_name="bar",
            tool_args={"x": 1},
        ),
    ]

    detector = ToolCallLoopDetector()
    instances = detector.detect(events)

    assert len(instances) == 0


def test_repeated_detector() -> None:
    """Test repeated identical calls detector."""
    events = [
        TraceEvent(
            timestamp="t1",
            type="tool_call",
            role="assistant",
            tool_name="foo",
            tool_args={"x": 1},
        ),
        TraceEvent(
            timestamp="t2",
            type="tool_call",
            role="assistant",
            tool_name="bar",
            tool_args={},
        ),
        TraceEvent(
            timestamp="t3",
            type="tool_call",
            role="assistant",
            tool_name="foo",
            tool_args={"x": 1},
        ),
        TraceEvent(
            timestamp="t4",
            type="tool_call",
            role="assistant",
            tool_name="foo",
            tool_args={"x": 1},
        ),
    ]

    detector = RepeatedIdenticalCallsDetector()
    instances = detector.detect(events)

    assert len(instances) == 1
    assert instances[0].details["tool"] == "foo"
    assert instances[0].details["count"] == 3


def test_retry_storm_five_errors() -> None:
    """Test retry storm with 5 consecutive errors."""
    events = [
        TraceEvent(timestamp="t1", type="tool_result", role="tool", error="err1"),
        TraceEvent(timestamp="t2", type="tool_result", role="tool", error="err2"),
        TraceEvent(timestamp="t3", type="tool_result", role="tool", error="err3"),
        TraceEvent(timestamp="t4", type="tool_result", role="tool", error="err4"),
        TraceEvent(timestamp="t5", type="tool_result", role="tool", error="err5"),
    ]

    detector = RetryStormDetector()
    instances = detector.detect(events)

    assert len(instances) == 1
    assert instances[0].details["error_count"] == 5


def test_retry_storm_four_then_success() -> None:
    """Test that 4 errors followed by success don't trigger storm."""
    events = [
        TraceEvent(timestamp="t1", type="tool_result", role="tool", error="err1"),
        TraceEvent(timestamp="t2", type="tool_result", role="tool", error="err2"),
        TraceEvent(timestamp="t3", type="tool_result", role="tool", error="err3"),
        TraceEvent(timestamp="t4", type="tool_result", role="tool", error="err4"),
        TraceEvent(timestamp="t5", type="tool_result", role="tool", content="ok"),
    ]

    detector = RetryStormDetector()
    instances = detector.detect(events)

    assert len(instances) == 0


def test_retry_storm_two_storms() -> None:
    """Test two separate storms."""
    events = [
        TraceEvent(timestamp="t1", type="tool_result", role="tool", error="err1"),
        TraceEvent(timestamp="t2", type="tool_result", role="tool", error="err2"),
        TraceEvent(timestamp="t3", type="tool_result", role="tool", error="err3"),
        TraceEvent(timestamp="t4", type="tool_result", role="tool", error="err4"),
        TraceEvent(timestamp="t5", type="tool_result", role="tool", error="err5"),
        TraceEvent(timestamp="t6", type="tool_result", role="tool", content="ok"),
        TraceEvent(timestamp="t7", type="tool_result", role="tool", error="err1"),
        TraceEvent(timestamp="t8", type="tool_result", role="tool", error="err2"),
        TraceEvent(timestamp="t9", type="tool_result", role="tool", error="err3"),
        TraceEvent(timestamp="t10", type="tool_result", role="tool", error="err4"),
        TraceEvent(timestamp="t11", type="tool_result", role="tool", error="err5"),
    ]

    detector = RetryStormDetector()
    instances = detector.detect(events)

    assert len(instances) == 2


def test_error_ignored_detected() -> None:
    """Test error-ignored with success claim."""
    events = [
        TraceEvent(timestamp="t1", type="tool_result", role="tool", error="Failed"),
        TraceEvent(
            timestamp="t2",
            type="message",
            role="assistant",
            content="Task completed successfully!",
        ),
    ]

    detector = ErrorIgnoredDetector()
    instances = detector.detect(events)

    assert len(instances) == 1
    assert instances[0].severity == "critical"


def test_error_ignored_retry_not_detected() -> None:
    """Test that retry after error is not detected."""
    events = [
        TraceEvent(timestamp="t1", type="tool_result", role="tool", error="Failed"),
        TraceEvent(
            timestamp="t2",
            type="tool_call",
            role="assistant",
            tool_name="retry",
            tool_args={},
        ),
        TraceEvent(
            timestamp="t3",
            type="message",
            role="assistant",
            content="Done",
        ),
    ]

    detector = ErrorIgnoredDetector()
    instances = detector.detect(events)

    assert len(instances) == 0


def test_error_ignored_case_insensitive() -> None:
    """Test that keywords are case-insensitive."""
    events = [
        TraceEvent(timestamp="t1", type="tool_result", role="tool", error="Failed"),
        TraceEvent(
            timestamp="t2",
            type="message",
            role="assistant",
            content="DONE with the task",
        ),
    ]

    detector = ErrorIgnoredDetector()
    instances = detector.detect(events)

    assert len(instances) == 1


def test_hallucinated_tool_unknown_detected(tmp_path: Path) -> None:
    """Test hallucinated tool detection."""
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps({"tools": ["known_tool", "another_tool"]}))

    events = [
        TraceEvent(
            timestamp="t1",
            type="tool_call",
            role="assistant",
            tool_name="unknown_tool",
            tool_args={},
        ),
    ]

    detector = HallucinatedToolDetector()
    instances = detector.detect(events, {"tools_catalog": str(catalog_path)})

    assert len(instances) == 1
    assert instances[0].details["tool"] == "unknown_tool"


def test_hallucinated_tool_all_known(tmp_path: Path) -> None:
    """Test that all known tools don't trigger detection."""
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps({"tools": ["known_tool"]}))

    events = [
        TraceEvent(
            timestamp="t1",
            type="tool_call",
            role="assistant",
            tool_name="known_tool",
            tool_args={},
        ),
    ]

    detector = HallucinatedToolDetector()
    instances = detector.detect(events, {"tools_catalog": str(catalog_path)})

    assert len(instances) == 0


def test_hallucinated_tool_no_catalog_skips() -> None:
    """Test that detector is skipped without catalog."""
    events = [
        TraceEvent(
            timestamp="t1",
            type="tool_call",
            role="assistant",
            tool_name="anything",
            tool_args={},
        ),
    ]

    detector = HallucinatedToolDetector()
    instances = detector.detect(events)

    assert len(instances) == 0


def test_token_blowup_cumulative() -> None:
    """Test token blowup on cumulative limit."""
    events = [
        TraceEvent(
            timestamp="t1",
            type="message",
            role="assistant",
            prompt_tokens=60_000,
            completion_tokens=60_000,
        ),
    ]

    detector = TokenBlowupDetector()
    instances = detector.detect(events)

    # Should trigger both single turn and cumulative
    assert len(instances) == 2


def test_token_blowup_single_turn() -> None:
    """Test token blowup on single turn."""
    events = [
        TraceEvent(
            timestamp="t1",
            type="message",
            role="assistant",
            prompt_tokens=30_000,
            completion_tokens=30_000,
        ),
    ]

    detector = TokenBlowupDetector()
    instances = detector.detect(events)

    assert len(instances) == 1
    assert instances[0].details["type"] == "single_turn"
    assert instances[0].details["tokens"] == 60_000


def test_token_blowup_not_detected() -> None:
    """Test that normal usage is not detected."""
    events = [
        TraceEvent(
            timestamp="t1",
            type="message",
            role="assistant",
            prompt_tokens=20_000,
            completion_tokens=20_000,
        ),
        TraceEvent(
            timestamp="t2",
            type="message",
            role="assistant",
            prompt_tokens=20_000,
            completion_tokens=20_000,
        ),
    ]

    detector = TokenBlowupDetector()
    instances = detector.detect(events)

    assert len(instances) == 0


def test_cost_blowup_detected() -> None:
    """Test cost blowup detection."""
    events = [
        TraceEvent(timestamp="t1", type="message", role="assistant", cost_usd=3.0),
        TraceEvent(timestamp="t2", type="message", role="assistant", cost_usd=3.0),
    ]

    detector = CostBlowupDetector()
    instances = detector.detect(events)

    assert len(instances) == 1
    assert instances[0].details["cost_usd"] == 6.0


def test_cost_blowup_not_detected() -> None:
    """Test that normal cost is not detected."""
    events = [
        TraceEvent(timestamp="t1", type="message", role="assistant", cost_usd=1.5),
        TraceEvent(timestamp="t2", type="message", role="assistant", cost_usd=1.5),
    ]

    detector = CostBlowupDetector()
    instances = detector.detect(events)

    assert len(instances) == 0


def test_latency_outlier_single_turn() -> None:
    """Test latency outlier on single turn."""
    events = [
        TraceEvent(timestamp="t1", type="message", role="assistant", latency_ms=12_000),
    ]

    detector = LatencyOutlierDetector()
    instances = detector.detect(events)

    assert len(instances) == 1
    assert instances[0].details["type"] == "single_turn"


def test_latency_outlier_p95() -> None:
    """Test latency outlier on P95."""
    events = [
        TraceEvent(timestamp=f"t{i}", type="message", role="assistant", latency_ms=6_000)
        for i in range(20)
    ]

    detector = LatencyOutlierDetector()
    instances = detector.detect(events)

    assert len(instances) == 1
    assert instances[0].details["type"] == "p95"


def test_latency_outlier_all_fast() -> None:
    """Test that fast latencies are not detected."""
    events = [
        TraceEvent(timestamp=f"t{i}", type="message", role="assistant", latency_ms=100)
        for i in range(20)
    ]

    detector = LatencyOutlierDetector()
    instances = detector.detect(events)

    assert len(instances) == 0
