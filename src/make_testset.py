# make_testset.py — generate the synthetic evaluation videos.
# Every scene is drawn with OpenCV itself on a plain background, so
# the test set is fully reproducible and honestly labelled SYNTHETIC.
# Each video is 640x360 at 10 fps. A matching JSON file records the
# ground-truth event (kind + the frame range where it happens) for
# every scene, so evaluation is mechanical, not eyeballed.

import json
import os

# Import OpenCV for drawing and video writing.
import cv2

# Import NumPy for blank frames.
import numpy as np

# Frame size used everywhere in this project.
WIDTH = 640
HEIGHT = 360
# Frames per second for every test video.
FPS = 10


# Draw one plain background frame (a light-grey room).
def blank_frame():
    # Fill the frame with a flat light grey.
    frame = np.full((HEIGHT, WIDTH, 3), 200, dtype=np.uint8)
    return frame


# Write a list of frames to an mp4 file.
def write_video(path, frames):
    # mp4v is the widely readable codec for .mp4 files.
    writer = cv2.VideoWriter(
        path, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (WIDTH, HEIGHT)
    )
    for frame in frames:
        writer.write(frame)
    writer.release()


# Every scene starts with 35 empty frames. That lead-in matters:
# the pipeline freezes its reference frame on frame 31, and the
# reference must show the empty room — otherwise the room's first
# occupant would be baked into "empty" and true shapes misread.
LEAD_IN = 35


# Scene 1: a person-like rectangle walks left to right, then stops.
# Ground truth: presence (tall, persistent, moving shape).
def scene_walk(out_dir):
    frames = []
    # The walker is 60 wide and 160 tall — a standing-person shape.
    for i in range(180):
        frame = blank_frame()
        if i >= LEAD_IN:
            # Walk from x=50 to x=450 across the scene.
            x = 50 + (i - LEAD_IN) * 3
            if x > 450:
                x = 450
            # Draw the walker as a dark rectangle.
            cv2.rectangle(frame, (x, 150), (x + 60, 310), (40, 40, 40), -1)
        frames.append(frame)
    write_video(os.path.join(out_dir, "walk.mp4"), frames)
    return {
        "file": "walk.mp4",
        "event": "presence",
        "frames": [LEAD_IN, 180],
        "note": "Empty room, then a tall rectangle walks across and stands.",
    }


# Scene 2: a person-like rectangle walks in, stands, then collapses.
# Ground truth: fall_like (tall shape suddenly low and wide).
def scene_fall(out_dir):
    frames = []
    for i in range(160):
        frame = blank_frame()
        if LEAD_IN <= i < 97:
            # Walk from x=50 toward x=300.
            x = 50 + (i - LEAD_IN) * 4
            if x > 300:
                x = 300
            cv2.rectangle(frame, (x, 150), (x + 60, 310), (40, 40, 40), -1)
        elif 97 <= i < 120:
            # Stand still at x=300.
            cv2.rectangle(frame, (300, 150), (360, 310), (40, 40, 40), -1)
        elif 120 <= i < 125:
            # Collapse over 5 frames: height shrinks, width grows.
            step = i - 120
            h = 160 - step * 28
            w = 60 + step * 20
            cv2.rectangle(frame, (300, 310 - h), (300 + w, 310), (40, 40, 40), -1)
        elif i >= 125:
            # Stay flat on the floor for the rest of the scene.
            cv2.rectangle(frame, (300, 270), (460, 310), (40, 40, 40), -1)
        frames.append(frame)
    write_video(os.path.join(out_dir, "fall.mp4"), frames)
    return {
        "file": "fall.mp4",
        "event": "fall_like",
        "frames": [120, 130],
        "note": "Walker enters, stands, collapses to a low wide shape, stays down.",
    }


# Scene 3: a person walks in, drops a small box, and walks away.
# Ground truth: left_object (small static box that remains).
def scene_package(out_dir):
    frames = []
    for i in range(180):
        frame = blank_frame()
        if LEAD_IN <= i < 85:
            # Walk from left toward x=200.
            x = 50 + (i - LEAD_IN) * 4
            if x > 200:
                x = 200
            cv2.rectangle(frame, (x, 150), (x + 60, 310), (40, 40, 40), -1)
        elif 85 <= i < 105:
            # Pause and "drop" the box just left of the walker.
            # The box sits on the LEFT side of the frame on purpose:
            # the stove zone is the bottom-right quarter, and a box
            # there would be excluded as glow cross-talk.
            cv2.rectangle(frame, (200, 150), (260, 310), (40, 40, 40), -1)
            cv2.rectangle(frame, (120, 260), (190, 310), (120, 80, 30), -1)
        elif 105 <= i < 145:
            # Walk away to the right, leaving the box behind.
            x = 200 + (i - 105) * 6
            cv2.rectangle(frame, (x, 150), (x + 60, 310), (40, 40, 40), -1)
            cv2.rectangle(frame, (120, 260), (190, 310), (120, 80, 30), -1)
        elif i >= 145:
            # Only the box remains, sitting still.
            cv2.rectangle(frame, (120, 260), (190, 310), (120, 80, 30), -1)
        frames.append(frame)
    write_video(os.path.join(out_dir, "package.mp4"), frames)
    return {
        "file": "package.mp4",
        "event": "left_object",
        "frames": [145, 180],
        "note": "Walker leaves a small box behind and exits; box stays.",
    }


# Scene 4: a bright orange-red glow appears in the stove zone.
# Ground truth: stove_glow (sustained glow, bottom-right quarter).
def scene_stove(out_dir):
    frames = []
    for i in range(140):
        frame = blank_frame()
        # No glow until frame 75, then a glowing ellipse.
        if i >= 75:
            # Bright orange-red ellipse in the stove zone.
            cv2.ellipse(frame, (500, 280), (60, 30), 0, 0, 360, (30, 100, 230), -1)
            # A brighter core makes the glow unmistakably hot-coloured.
            cv2.ellipse(frame, (500, 280), (30, 15), 0, 0, 360, (20, 60, 250), -1)
        frames.append(frame)
    write_video(os.path.join(out_dir, "stove.mp4"), frames)
    return {
        "file": "stove.mp4",
        "event": "stove_glow",
        "frames": [75, 140],
        "note": "Orange-red glow appears in the stove zone and stays.",
    }


# Scene 5: nothing happens at all — the negative control.
# Ground truth: no event (any alert here is a false positive).
def scene_empty(out_dir):
    frames = [blank_frame() for _ in range(120)]
    write_video(os.path.join(out_dir, "empty.mp4"), frames)
    return {
        "file": "empty.mp4",
        "event": None,
        "frames": [0, 120],
        "note": "Empty room. Any event here is a false positive.",
    }


# Scene 6: sudden lighting change — the failure case.
# Ground truth: no event (a global brightness shift is not motion
# worth alerting on, but naive background subtraction may fire).
def scene_lighting(out_dir):
    frames = []
    for i in range(120):
        # The whole room gets darker halfway through.
        level = 200 if i < 60 else 140
        frame = np.full((HEIGHT, WIDTH, 3), level, dtype=np.uint8)
        frames.append(frame)
    write_video(os.path.join(out_dir, "lighting.mp4"), frames)
    return {
        "file": "lighting.mp4",
        "event": None,
        "frames": [0, 120],
        "note": "Global lighting change only. Motion here is a false positive.",
    }


# Build every scene and write the ground-truth manifest.
def main(out_dir):
    # Create the output folder if it does not exist yet.
    os.makedirs(out_dir, exist_ok=True)
    scenes = [
        scene_walk(out_dir),
        scene_fall(out_dir),
        scene_package(out_dir),
        scene_stove(out_dir),
        scene_empty(out_dir),
        scene_lighting(out_dir),
    ]
    # The manifest is what evaluation scores against.
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(scenes, f, indent=2)
    print(f"Wrote {len(scenes)} scenes to {out_dir}")


# Run the generator when this file is executed directly.
if __name__ == "__main__":
    import sys

    # Default output folder sits next to this file's project.
    target = sys.argv[1] if len(sys.argv) > 1 else "evaluation/testset"
    main(target)
