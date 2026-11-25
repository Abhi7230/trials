"""Tests for scenario replay."""

import json
import pytest


def test_replay_dinner_scenario():
    """Test replaying dinner scenario."""
    from agent_ledger.replay import replay_file
    
    exit_code = replay_file("examples/dinner.yaml", ":memory:", "json")
    assert exit_code == 0


def test_replay_policy_walkthrough():
    """Test replaying policy walkthrough."""
    from agent_ledger.replay import replay_file
    
    exit_code = replay_file("examples/policy_walkthrough.yaml", ":memory:", "json")
    # This may fail some steps, but should not crash
    assert exit_code in [0, 1]


def test_replay_deterministic():
    """Test replay produces deterministic output."""
    from agent_ledger.replay import replay_file
    import sys
    from io import StringIO
    
    # Capture output from two runs
    old_stdout = sys.stdout
    
    sys.stdout = StringIO()
    replay_file("examples/policy_walkthrough.yaml", ":memory:", "json")
    output1 = sys.stdout.getvalue()
    
    sys.stdout = StringIO()
    replay_file("examples/policy_walkthrough.yaml", ":memory:", "json")
    output2 = sys.stdout.getvalue()
    
    sys.stdout = old_stdout
    
    # Outputs should be identical
    assert output1 == output2
