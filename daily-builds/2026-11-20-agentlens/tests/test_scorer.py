"""Tests for scorer."""

from agentlens.models import TraceEvent
from agentlens.scorer import analyze_trace


def test_perfect_trace_scores_100() -> None:
    """Test that a perfect trace scores 100."""
    events = [
        TraceEvent(timestamp="t1", type="message", role="user", content="Hello"),
        TraceEvent(timestamp="t2", type="message", role="assistant", content="Hi"),
    ]

    result = analyze_trace(events)
    assert result.score == 100
    assert len(result.patterns) == 0


def test_one_loop_scores_85() -> None:
    """Test that one loop deducts 15 points."""
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
        TraceEvent(
            timestamp="t4",
            type="tool_call",
            role="assistant",
            tool_name="foo",
            tool_args={"x": 1},
        ),
    ]

    result = analyze_trace(events)
    assert result.score == 85
    assert len(result.patterns) == 1


def test_loop_and_error_ignored_scores_60() -> None:
    """Test that loop + error-ignored = 60."""
    events = [
        # Loop (4 calls)
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
        TraceEvent(
            timestamp="t4",
            type="tool_call",
            role="assistant",
            tool_name="foo",
            tool_args={"x": 1},
        ),
        # Error ignored
        TraceEvent(timestamp="t5", type="tool_result", role="tool", error="Failed"),
        TraceEvent(
            timestamp="t6",
            type="message",
            role="assistant",
            content="Done!",
        ),
    ]

    result = analyze_trace(events)
    # 100 - 25 (error-ignored, critical, sorted first) - 15 (loop) = 60
    assert result.score == 60
    assert len(result.patterns) == 2


def test_floor_at_zero() -> None:
    """Test that score floors at 0."""
    events = [
        # Multiple critical errors
        TraceEvent(timestamp="t1", type="tool_result", role="tool", error="err1"),
        TraceEvent(
            timestamp="t2",
            type="message",
            role="assistant",
            content="Success!",
        ),
        TraceEvent(timestamp="t3", type="tool_result", role="tool", error="err2"),
        TraceEvent(
            timestamp="t4",
            type="message",
            role="assistant",
            content="Done!",
        ),
        TraceEvent(timestamp="t5", type="tool_result", role="tool", error="err3"),
        TraceEvent(
            timestamp="t6",
            type="message",
            role="assistant",
            content="Completed!",
        ),
        TraceEvent(timestamp="t7", type="tool_result", role="tool", error="err4"),
        TraceEvent(
            timestamp="t8",
            type="message",
            role="assistant",
            content="Finished!",
        ),
    ]

    result = analyze_trace(events)
    assert result.score == 0


def test_severity_ordering() -> None:
    """Test that patterns are sorted by severity."""
    events = [
        # Low severity (repeated)
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
        # Critical (error-ignored)
        TraceEvent(timestamp="t4", type="tool_result", role="tool", error="Failed"),
        TraceEvent(
            timestamp="t5",
            type="message",
            role="assistant",
            content="Success!",
        ),
    ]

    result = analyze_trace(events)
    # Critical should be deducted first: 100 - 25 - 5 = 70
    assert result.score == 70
