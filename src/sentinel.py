# sentinel.py — the OpenCV 5 perception pipeline for Hearthwatch.
# It reads one video frame at a time and returns structured detections.
# No machine-learning model is used: every detector below is classical
# computer vision (background subtraction, contours, colour), which keeps
# the pipeline explainable and runnable on any CPU.

import math

# Import OpenCV. The pinned version is 5.0.0 (see requirements.txt).
import cv2

# Import NumPy for fast array math on image pixels.
import numpy as np


# A detection is one thing the pipeline noticed in one frame.
# kind: what kind of thing ("motion", "presence", "left_object",
#       "stove_glow", "fall_like").
# x, y, w, h: the bounding box of the thing, in pixels.
# score: a 0-to-1 confidence-ish number (see each detector's comment).
# track_id: which tracked object this belongs to, or None.
class Detection:
    # Store the detection's fields for later use by the agent.
    def __init__(self, kind, x, y, w, h, score, track_id=None):
        self.kind = kind
        self.x = int(x)
        self.y = int(y)
        self.w = int(w)
        self.h = int(h)
        self.score = float(score)
        self.track_id = track_id

    # Turn the detection into a plain dictionary for JSON output.
    def to_dict(self):
        return {
            "kind": self.kind,
            "x": self.x,
            "y": self.y,
            "w": self.w,
            "h": self.h,
            "score": round(self.score, 3),
            "track_id": self.track_id,
        }


# One tracked object: a blob the pipeline has followed across frames.
# Keeping identity across frames is what turns flickering detections
# into events (a fall is a change in ONE track over time, not noise).
class Track:
    # Start a new track at the given bounding box.
    def __init__(self, track_id, x, y, w, h):
        self.track_id = track_id
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        # Centre of the box, used to match this track to new boxes.
        self.cx = x + w / 2.0
        self.cy = y + h / 2.0
        # How many frames this track has lived (persistence filter).
        self.age = 1
        # How many frames since this track was last matched.
        self.missed = 0
        # Height-to-width history, used to spot a fall-like collapse.
        self.aspect_history = [h / max(w, 1)]
        # Whether this track has already produced a fall-like event.
        self.fall_reported = False
        # Whether this track has already produced a presence event.
        self.presence_reported = False

    # Move the track to a newly matched bounding box.
    def update(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.cx = x + w / 2.0
        self.cy = y + h / 2.0
        self.age += 1
        self.missed = 0
        # Remember the newest shape, keeping only the last 30 frames.
        self.aspect_history.append(h / max(w, 1))
        self.aspect_history = self.aspect_history[-30:]

    # Return True when the track's shape collapsed recently.
    # A standing shape is tall (aspect above ~1.2); a fallen shape is
    # low and wide (aspect below ~0.7). A fast drop between the two
    # inside a few frames is a fall-like candidate, not a diagnosis.
    def collapsed(self):
        # Need at least 5 frames of history to judge a change.
        if len(self.aspect_history) < 5:
            return False
        # Compare the recent shape to the shape a few frames ago.
        before = self.aspect_history[-5]
        now = self.aspect_history[-1]
        return before >= 1.2 and now <= 0.7


# The perception pipeline: one object holds all the OpenCV state.
class Sentinel:
    # Set up the pipeline for frames of a given size.
    # width, height: expected frame size in pixels (used for zones).
    # min_area: blobs smaller than this (in pixels) are ignored as noise.
    def __init__(self, width=640, height=360, min_area=1200):
        self.width = width
        self.height = height
        self.min_area = min_area
        # MOG2 learns what the background looks like and reports only
        # pixels that differ from it — that is the motion signal.
        # history=200 means it adapts over about 200 frames.
        # varThreshold=25 sets how different a pixel must be to count.
        # detectShadows=False keeps shadows from becoming fake blobs.
        self.back_sub = cv2.createBackgroundSubtractorMOG2(
            history=200, varThreshold=25, detectShadows=False
        )
        # A 5x5 block used to clean up the motion mask (close holes,
        # drop specks) before contours are measured.
        self.kernel = np.ones((5, 5), np.uint8)
        # All live tracks, keyed by track id.
        self.tracks = {}
        # Counter for handing out fresh track ids.
        self.next_track_id = 1
        # Frame counter, used to warm up the background model.
        self.frame_no = 0
        # How long a new static blob must sit still before it counts
        # as a "left object" (in frames, at ~10 fps this is ~3 seconds
        # of stillness after motion stops — tuned in evaluation).
        self.left_object_frames = 30
        # A reference frame, frozen after warm-up, used to spot static
        # objects: something present now but absent at session start.
        # (A moving blob vanishes from the motion mask once it stops,
        # so motion alone can never report a left object — the frozen
        # reference is what makes left-object detection possible.)
        self.reference = None
        # Still counters for static blobs, keyed by rounded position.
        self.still_blobs = {}
        # Static blobs already reported, so each is reported once.
        self.reported_static = set()
        # The stove zone is the bottom-right quarter of the frame by
        # default; deployments override it to cover the real stove.
        self.stove_zone = (
            int(width * 0.55),
            int(height * 0.55),
            width,
            height,
        )

    # Let a deployment point the stove zone at the real stove.
    # x0, y0, x1, y1 are pixel coordinates of the zone's corners.
    def set_stove_zone(self, x0, y0, x1, y1):
        self.stove_zone = (int(x0), int(y0), int(x1), int(y1))

    # Find moving blobs in one frame and return their bounding boxes.
    # frame: a colour image (NumPy array) in BGR order, as OpenCV uses.
    def _moving_boxes(self, frame):
        # Ask MOG2 for the motion mask of this frame.
        mask = self.back_sub.apply(frame)
        # Fill small holes inside blobs so one object is one contour.
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.kernel)
        # Drop isolated specks smaller than the kernel can bridge.
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)
        # Trace the outline of each white region in the mask.
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        boxes = []
        # Turn each contour into a box, skipping tiny noise blobs.
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_area:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            boxes.append((x, y, w, h, area))
        return boxes

    # Measure how much of the stove zone glows like a hot burner.
    # A burner glows bright orange-red: high red, medium green, low
    # blue, and bright overall. Returns a 0-to-1 glow fraction.
    def _stove_glow(self, frame):
        # Cut out just the stove zone from the frame.
        x0, y0, x1, y1 = self.stove_zone
        zone = frame[y0:y1, x0:x1]
        # An empty zone (bad coordinates) cannot glow.
        if zone.size == 0:
            return 0.0
        # Split the zone into blue, green, red channels.
        blue = zone[:, :, 0].astype(int)
        green = zone[:, :, 1].astype(int)
        red = zone[:, :, 2].astype(int)
        # A pixel counts as glow when red is clearly strongest and
        # the pixel is bright — this rejects ordinary red objects.
        glow_pixels = ((red > 150) & (red > green + 40) & (red > blue + 60))
        # The fraction is glowing pixels over all zone pixels.
        return float(glow_pixels.mean())

    # Match new boxes to existing tracks by nearest centre.
    # Unmatched boxes start new tracks; unmatched tracks age out.
    def _update_tracks(self, boxes):
        # Centres of the new boxes, for distance matching.
        used = set()
        # For each track, find the closest unused new box.
        for track in list(self.tracks.values()):
            best = None
            best_dist = 1e9
            for i, (x, y, w, h, _area) in enumerate(boxes):
                if i in used:
                    continue
                cx = x + w / 2.0
                cy = y + h / 2.0
                dist = math.hypot(cx - track.cx, cy - track.cy)
                if dist < best_dist:
                    best_dist = dist
                    best = i
            # A match must be reasonably close (within 120 pixels),
            # otherwise the track is a different object.
            if best is not None and best_dist < 120:
                x, y, w, h, _area = boxes[best]
                track.update(x, y, w, h)
                used.add(best)
            else:
                # No match: the track may have left the frame.
                track.missed += 1
        # Drop tracks that have been unmatched for 10 frames.
        for tid in [t for t, tr in self.tracks.items() if tr.missed > 10]:
            del self.tracks[tid]
        # Every unused box becomes a brand-new track.
        for i, (x, y, w, h, _area) in enumerate(boxes):
            if i in used:
                continue
            tid = self.next_track_id
            self.next_track_id += 1
            self.tracks[tid] = Track(tid, x, y, w, h)

    # Find static new objects: boxes that differ from the frozen
    # reference frame. Returns a list of (x, y, w, h) boxes.
    def _static_boxes(self, frame):
        # Freeze the reference on the first frame after warm-up.
        # Test scenes (and a real deployment) start on an empty room,
        # so the reference is the empty scene.
        if self.reference is None and self.frame_no == 31:
            self.reference = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.reference is None:
            return []
        # Grey version of the current frame, for comparison.
        grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Absolute difference: bright where the scene changed.
        diff = cv2.absdiff(grey, self.reference)
        # Keep only strong changes (ignore sensor noise).
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, self.kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, self.kernel)
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        boxes = []
        for contour in contours:
            if cv2.contourArea(contour) < self.min_area:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            boxes.append((x, y, w, h))
        return boxes

    # Run the full pipeline on one frame and return detections.
    # Warm-up: the first 30 frames only train the background model,
    # because MOG2 reports everything as motion before it has learned
    # what "still" looks like.
    def process(self, frame):
        self.frame_no += 1
        # Shrink or grow the frame to the pipeline's expected size.
        if (frame.shape[1], frame.shape[0]) != (self.width, self.height):
            frame = cv2.resize(frame, (self.width, self.height))
        # Motion boxes come from MOG2; static boxes come from the
        # frozen reference. Merged, they describe true object shapes:
        # a motion blob during a fall is only the changed region,
        # while the static box is the person's real current shape.
        # Static boxes win on overlap (true shape over change region).
        motion_boxes = self._moving_boxes(frame)
        static_boxes = self._static_boxes(frame)
        boxes = [(x, y, w, h, w * h) for (x, y, w, h) in static_boxes]
        for (x, y, w, h, area) in motion_boxes:
            cx = x + w / 2.0
            cy = y + h / 2.0
            # Skip motion boxes that overlap a static box: the static
            # box already describes that object more accurately.
            overlaps = any(
                abs(cx - (sx + sw / 2.0)) < 40
                and abs(cy - (sy + sh / 2.0)) < 40
                for (sx, sy, sw, sh) in static_boxes
            )
            if not overlaps:
                boxes.append((x, y, w, h, area))
        self._update_tracks(boxes)
        # During warm-up, report nothing — the model is still learning.
        if self.frame_no <= 30:
            return []
        detections = []
        # Motion: every moving blob is a low-level detection.
        for (x, y, w, h, area) in boxes:
            # Score scales with blob size, capped at 1.
            score = min(1.0, area / 20000.0)
            detections.append(Detection("motion", x, y, w, h, score))
        # Presence: a track that is tall, big, and persistent looks
        # like a person standing — a heuristic, labelled as such.
        for track in self.tracks.values():
            aspect = track.h / max(track.w, 1)
            area = track.w * track.h
            if (
                track.age >= 10
                and aspect >= 1.2
                and area >= self.min_area
                and not track.presence_reported
            ):
                track.presence_reported = True
                detections.append(
                    Detection(
                        "presence",
                        track.x,
                        track.y,
                        track.w,
                        track.h,
                        0.7,
                        track.track_id,
                    )
                )
            # Fall-like: a tracked tall shape that collapsed.
            if track.collapsed() and not track.fall_reported:
                track.fall_reported = True
                detections.append(
                    Detection(
                        "fall_like",
                        track.x,
                        track.y,
                        track.w,
                        track.h,
                        0.8,
                        track.track_id,
                    )
                )
        # Left object: a static box that is short, not currently
        # moving, and has sat still long enough.
        # Boxes where a fall was already reported are excluded: a
        # fallen body is short and still, but it is explained by the
        # fall event — reporting it again as a "package" would be a
        # duplicate alert for one real-world thing.
        fall_boxes = [
            (t.x, t.y, t.w, t.h)
            for t in self.tracks.values()
            if t.fall_reported
        ]
        current_keys = set()
        for (x, y, w, h) in static_boxes:
            # Skip boxes inside the stove zone: a glow patch there is
            # short and static, so it would otherwise double-report
            # as a "package". The glow event already explains it.
            cx0 = x + w / 2.0
            cy0 = y + h / 2.0
            zx0, zy0, zx1, zy1 = self.stove_zone
            if zx0 <= cx0 <= zx1 and zy0 <= cy0 <= zy1:
                continue
            # Skip boxes explained by an earlier fall event.
            cx = x + w / 2.0
            cy = y + h / 2.0
            if any(
                abs(cx - (fx + fw / 2.0)) < 80
                and abs(cy - (fy + fh / 2.0)) < 80
                for (fx, fy, fw, fh) in fall_boxes
            ):
                continue
            # Skip tall blobs: a standing person is tall, and a
            # person pausing must not become a "package". This
            # height guard is a documented heuristic, not a
            # classifier — it trades some recall for fewer
            # false left-object alerts on still people.
            if h >= 100:
                continue
            # Skip blobs that are currently moving: those are
            # people or pets, not left objects. (Checked against the
            # MOTION boxes only — the merged list contains this very
            # static box, which would otherwise always match itself.)
            moving = any(
                abs(x - bx) < 40 and abs(y - by) < 40
                for (bx, by, _bw, _bh, _a) in motion_boxes
            )
            if moving:
                continue
            key = (round(x / 20), round(y / 20))
            current_keys.add(key)
            self.still_blobs[key] = self.still_blobs.get(key, 0) + 1
            # Report once the blob has sat still long enough.
            if (
                self.still_blobs[key] >= self.left_object_frames
                and key not in self.reported_static
            ):
                self.reported_static.add(key)
                detections.append(
                    Detection("left_object", x, y, w, h, 0.75)
                )
        # Prune still blobs that are gone from the scene.
        for key in [k for k in self.still_blobs if k not in current_keys]:
            del self.still_blobs[key]
        # Stove glow: a sustained bright orange-red patch in the zone.
        glow = self._stove_glow(frame)
        if glow > 0.02:
            x0, y0, x1, y1 = self.stove_zone
            detections.append(
                Detection(
                    "stove_glow",
                    x0,
                    y0,
                    x1 - x0,
                    y1 - y0,
                    min(1.0, glow * 10.0),
                )
            )
        return detections
