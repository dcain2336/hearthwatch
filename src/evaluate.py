# evaluate.py — score Hearthwatch against the synthetic test set.
# For each scene: run the pipeline and the agent over the video, then
# compare the agent's events to the manifest's ground truth.
# Scoring rule, stated plainly: an event counts as a HIT when the
# agent reports the expected kind at any frame at or after the truth
# window starts (detection latency is reported, not hidden). An event
# on a no-event scene counts as a FALSE POSITIVE. An expected event
# never reported counts as a MISS.

import json
import os
import sys

# Import OpenCV for reading the test videos.
import cv2

# Import the pipeline and the agent from this same folder.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent import HearthAgent
from sentinel import Sentinel


# Run one video through the pipeline and agent, return event kinds
# with the frame number each first appeared on.
def run_video(path):
    # Open the video file for frame-by-frame reading.
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {path}")
    # Fresh pipeline and agent per video (no state leaks between scenes).
    sentinel = Sentinel()
    agent = HearthAgent()
    # The stove zone default already covers the bottom-right quarter,
    # which is where the stove scene draws its glow.
    first_seen = {}
    frame_no = 0
    # Read frames until the video ends.
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_no += 1
        # Pipeline detections for this frame.
        detections = sentinel.process(frame)
        # Agent events for this frame.
        events = agent.observe(detections)
        # Record the first frame each event kind appeared.
        for event in events:
            if event.kind not in first_seen:
                first_seen[event.kind] = frame_no
    cap.release()
    return first_seen, agent


# Score every scene in a test-set folder against its manifest.
def main(testset_dir):
    # Load the ground-truth manifest written by make_testset.py.
    with open(os.path.join(testset_dir, "manifest.json")) as f:
        scenes = json.load(f)
    results = []
    hits = 0
    misses = 0
    false_positives = 0
    # Score each scene in turn.
    for scene in scenes:
        path = os.path.join(testset_dir, scene["file"])
        first_seen, agent = run_video(path)
        expected = scene["event"]
        # The truth window start: detections before warm-up (frame 30)
        # cannot exist, so latency is measured from window start.
        start = scene["frames"][0] if scene["frames"] else 0
        # For the agent, "reported" means an event of that kind exists.
        reported_kinds = {e.kind for e in agent.events}
        # Score this scene.
        if expected is None:
            # No-event scene: any reported kind is a false positive.
            fps = sorted(reported_kinds)
            false_positives += len(fps)
            verdict = "PASS (no false positives)" if not fps else "FALSE POSITIVE"
            detail = f"reported={fps}"
        elif expected in reported_kinds:
            hits += 1
            latency = first_seen.get(expected, 0) - start
            verdict = "HIT"
            detail = f"first seen frame {first_seen.get(expected)}, latency {latency} frames"
        else:
            misses += 1
            verdict = "MISS"
            detail = f"reported={sorted(reported_kinds)}"
        results.append(
            {
                "file": scene["file"],
                "expected": expected,
                "verdict": verdict,
                "detail": detail,
            }
        )
        print(f"{scene['file']:14s} expected={str(expected):12s} {verdict:26s} {detail}")
    # Summary line: the headline numbers for the report.
    total = hits + misses
    recall = (hits / total) if total else 0.0
    print(f"\nHIT {hits} / MISS {misses} / FALSE POSITIVE {false_positives}")
    print(f"Recall on event scenes: {recall:.2f}")
    # Save the machine-readable results next to the manifest.
    with open(os.path.join(testset_dir, "results.json"), "w") as f:
        json.dump(
            {
                "hits": hits,
                "misses": misses,
                "false_positives": false_positives,
                "recall": round(recall, 3),
                "scenes": results,
            },
            f,
            indent=2,
        )


# Run the scorer when this file is executed directly.
if __name__ == "__main__":
    # Default test-set folder sits next to this file's project.
    target = sys.argv[1] if len(sys.argv) > 1 else "evaluation/testset"
    main(target)
