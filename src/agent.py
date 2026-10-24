# agent.py — the decision loop for Hearthwatch.
# The pipeline (sentinel.py) reports detections; this module turns
# them into events, scores risk, picks actions, and then VERIFIES its
# own actions by re-observing. That perception-decision-action loop,
# with vision output changing later decisions, is what makes this an
# Agentic Vision entry rather than a detector with a speaker.

import time


# One event: something the household should know about.
# kind matches the detection kind ("presence", "left_object",
# "stove_glow", "fall_like", "motion").
# tier: "log" (record only), "notify" (tell the household),
#       "escalate" (urgent, needs acknowledgement).
# state: "open", "acknowledged", "resolved", "false_alarm".
class Event:
    # Store the event's fields.
    def __init__(self, kind, tier, score, detail):
        self.kind = kind
        self.tier = tier
        self.score = score
        self.detail = detail
        self.state = "open"
        # Unix time the event was created.
        self.created = time.time()
        # Unix time the event was last re-observed, or None.
        self.last_seen = None
        # How many times the event has been re-observed.
        self.observations = 1

    # Turn the event into a plain dictionary for JSON output.
    def to_dict(self):
        return {
            "kind": self.kind,
            "tier": self.tier,
            "score": round(self.score, 3),
            "detail": self.detail,
            "state": self.state,
            "observations": self.observations,
        }


# The agent: holds alert state, thresholds, and feedback learning.
class HearthAgent:
    # Set up the agent with default thresholds.
    # glow_frames: how many consecutive glow frames before a
    #   stove alert (prevents one bright frame from alarming).
    # fall_cooldown: seconds before the same track can re-alert.
    def __init__(self, glow_frames=5, fall_cooldown=30):
        # All events, newest last.
        self.events = []
        # Open alerts the household has not yet handled.
        self.open_alerts = []
        # Consecutive frames of stove glow seen so far.
        self.glow_streak = 0
        self.glow_frames = glow_frames
        # Whether a stove alert is already open (avoid duplicates).
        self.glow_alert_open = False
        # Thresholds the household's feedback can nudge.
        # motion_area: blobs smaller than this never become events.
        # glow_fraction: stove-zone glow fraction that counts.
        self.thresholds = {
            "motion_area": 1200,
            "glow_fraction": 0.02,
        }
        # Count of false alarms, used to show learning over time.
        self.false_alarms = 0
        # Last time a fall alert fired, for cooldown.
        self.last_fall_time = 0
        self.fall_cooldown = fall_cooldown

    # Decide the action tier for a detection kind and score.
    # A fall-like event is always an escalation: a person may be hurt.
    # A stove glow is a notification: a hazard that can still be fixed.
    # A left object is a notification: worth knowing, not urgent.
    # A presence is a log entry: routine household movement.
    def _tier_for(self, kind):
        if kind == "fall_like":
            return "escalate"
        if kind in ("stove_glow", "left_object"):
            return "notify"
        return "log"

    # Feed one frame's detections into the agent and return any
    # NEW events created this frame (re-observations update existing
    # events in place and return nothing new).
    def observe(self, detections):
        new_events = []
        # Track whether glow was seen this frame (for streak logic).
        glow_seen = False
        for det in detections:
            # Motion detections are too low-level to become events on
            # their own — they feed the trackers, not the household.
            if det.kind == "motion":
                continue
            # Stove glow needs a streak: one bright frame could be a
            # camera glitch or a passing reflection, not a burner.
            if det.kind == "stove_glow":
                glow_seen = True
                self.glow_streak += 1
                # Only alert once the streak is long enough and no
                # glow alert is already open.
                if self.glow_streak >= self.glow_frames and not self.glow_alert_open:
                    self.glow_alert_open = True
                    event = Event(
                        "stove_glow",
                        "notify",
                        det.score,
                        "Sustained glow in the stove zone — burner may be on.",
                    )
                    self._open(event)
                    new_events.append(event)
                continue
            # Fall-like events respect a cooldown so one fall does
            # not produce a burst of duplicate escalations.
            if det.kind == "fall_like":
                now = time.time()
                if now - self.last_fall_time < self.fall_cooldown:
                    continue
                self.last_fall_time = now
            # Every other detection kind becomes an event at once.
            event = Event(
                det.kind,
                self._tier_for(det.kind),
                det.score,
                self._detail_for(det),
            )
            self._open(event)
            new_events.append(event)
        # A frame with no glow breaks the streak and, if the glow
        # alert was open, marks it resolved: the burner went off.
        # This is the verification step — the agent checks its own
        # alert against fresh vision instead of assuming it persists.
        if not glow_seen:
            self.glow_streak = 0
            if self.glow_alert_open:
                self.glow_alert_open = False
                for event in self.open_alerts:
                    if event.kind == "stove_glow":
                        event.state = "resolved"
                # Resolved alerts leave the open list.
                self.open_alerts = [
                    e for e in self.open_alerts if e.state == "open"
                ]
        return new_events

    # Write a human-readable detail line for a detection.
    def _detail_for(self, det):
        if det.kind == "presence":
            return "Person-like presence in view (shape and motion heuristic)."
        if det.kind == "left_object":
            return "Small static object appeared and stayed — possibly a package."
        if det.kind == "fall_like":
            return "Fall-like collapse: a tracked tall shape suddenly went low and wide."
        return "Unclassified detection."

    # Record a new event in both the history and the open list.
    def _open(self, event):
        self.events.append(event)
        if event.tier in ("notify", "escalate"):
            self.open_alerts.append(event)

    # A household member acknowledges an open alert.
    # alert_index: position in the open-alert list.
    # Returns True when an alert was acknowledged.
    def acknowledge(self, alert_index):
        if 0 <= alert_index < len(self.open_alerts):
            self.open_alerts[alert_index].state = "acknowledged"
            del self.open_alerts[alert_index]
            return True
        return False

    # A household member marks an open alert a false alarm.
    # The feedback nudges thresholds upward (less sensitive) so the
    # same mistake gets rarer — bounded, so one person's taps can
    # never silence the system entirely.
    # alert_index: position in the open-alert list.
    # Returns True when an alert was marked false.
    def mark_false_alarm(self, alert_index):
        if 0 <= alert_index < len(self.open_alerts):
            event = self.open_alerts[alert_index]
            event.state = "false_alarm"
            del self.open_alerts[alert_index]
            self.false_alarms += 1
            # Nudge the matching threshold up by 10%, capped at 2x
            # its starting value, so feedback helps but never mutes.
            if event.kind == "stove_glow":
                key = "glow_fraction"
            else:
                key = "motion_area"
            start = 0.02 if key == "glow_fraction" else 1200
            self.thresholds[key] = min(
                start * 2.0, self.thresholds[key] * 1.10
            )
            return True
        return False

    # Summarise the agent's current state for the dashboard.
    def status(self):
        return {
            "total_events": len(self.events),
            "open_alerts": [e.to_dict() for e in self.open_alerts],
            "false_alarms": self.false_alarms,
            "thresholds": self.thresholds,
        }
