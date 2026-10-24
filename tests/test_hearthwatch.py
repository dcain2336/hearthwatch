# test_hearthwatch.py — unit tests for Hearthwatch.
# Run with: python3 tests/test_hearthwatch.py
# No test framework is needed: each test is a function, and main()
# runs them all and reports failures plainly.

import os
import sys

# Import NumPy for building synthetic frames.
import numpy as np

# Make the src folder importable from this test file.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from agent import HearthAgent
from sentinel import Detection, Sentinel, Track


# Test: a track's shape collapse is detected correctly.
def test_track_collapse():
    # Start a tall track (160 tall, 60 wide).
    track = Track(1, 300, 150, 60, 160)
    # Feed it 5 frames of tall shape, then a flat shape.
    for _ in range(4):
        track.update(300, 150, 60, 160)
    track.update(300, 270, 160, 40)
    # The track should now report a collapse.
    assert track.collapsed(), "tall-to-flat track should report collapsed"


# Test: a track that stays tall never reports a collapse.
def test_track_no_collapse_when_tall():
    track = Track(1, 300, 150, 60, 160)
    for _ in range(10):
        track.update(300, 150, 60, 160)
    assert not track.collapsed(), "steady tall track must not report collapsed"


# Test: warm-up frames produce no detections at all.
def test_warmup_silent():
    sentinel = Sentinel()
    # A plain grey frame, repeated: nothing should be reported
    # during the first 30 frames while the model learns.
    frame = np.full((360, 640, 3), 200, dtype=np.uint8)
    for _ in range(30):
        assert sentinel.process(frame) == [], "warm-up must stay silent"


# Test: the agent escalates a fall-like detection.
def test_agent_escalates_fall():
    agent = HearthAgent()
    events = agent.observe([Detection("fall_like", 300, 270, 160, 40, 0.8, 1)])
    assert len(events) == 1, "fall_like should create one event"
    assert events[0].tier == "escalate", "fall_like must escalate"


# Test: stove glow needs a streak before alerting.
def test_agent_glow_streak():
    agent = HearthAgent(glow_frames=5)
    glow = Detection("stove_glow", 350, 200, 290, 160, 0.5)
    # Four frames of glow: still no alert.
    for _ in range(4):
        assert agent.observe([glow]) == [], "glow streak too short to alert"
    # Fifth frame: the alert fires.
    events = agent.observe([glow])
    assert len(events) == 1, "glow streak complete should alert"


# Test: a cleared glow resolves the open alert (verification step).
def test_agent_glow_resolves():
    agent = HearthAgent(glow_frames=1)
    glow = Detection("stove_glow", 350, 200, 290, 160, 0.5)
    agent.observe([glow])
    assert len(agent.open_alerts) == 1, "glow alert should be open"
    # A frame with no detections means the glow is gone.
    agent.observe([])
    assert len(agent.open_alerts) == 0, "cleared glow must resolve the alert"
    assert agent.events[0].state == "resolved", "resolved state must be recorded"


# Test: false-alarm feedback nudges thresholds but never mutes.
def test_agent_false_alarm_learning():
    agent = HearthAgent(glow_frames=1)
    glow = Detection("stove_glow", 350, 200, 290, 160, 0.5)
    agent.observe([glow])
    before = agent.thresholds["glow_fraction"]
    assert agent.mark_false_alarm(0), "marking should succeed"
    after = agent.thresholds["glow_fraction"]
    assert after > before, "threshold must rise after a false alarm"
    assert after <= 0.04, "threshold must be capped at 2x its start"


# Test: acknowledging an alert removes it from the open list.
def test_agent_acknowledge():
    agent = HearthAgent()
    agent.observe([Detection("fall_like", 300, 270, 160, 40, 0.8, 1)])
    assert agent.acknowledge(0), "acknowledge should succeed"
    assert len(agent.open_alerts) == 0, "acknowledged alert must leave open list"


# Run every test function and report the result.
def main():
    tests = [
        test_track_collapse,
        test_track_no_collapse_when_tall,
        test_warmup_silent,
        test_agent_escalates_fall,
        test_agent_glow_streak,
        test_agent_glow_resolves,
        test_agent_false_alarm_learning,
        test_agent_acknowledge,
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {test.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} tests passed")
    # Exit non-zero when any test failed, so CI-style runs catch it.
    sys.exit(1 if failed else 0)


# Run the tests when this file is executed directly.
if __name__ == "__main__":
    main()
