# Hearthwatch — a home-safety vision agent

## The problem, in one sentence
A camera watches a home, but nobody watches the camera — so a fall, a
stove left glowing, or a package left at the door is only noticed when
it is already too late.

## What Hearthwatch does
Hearthwatch turns a plain camera feed into an agent that perceives,
decides, and acts — and then checks its own work:

1. **Perceive (OpenCV 5).** Every frame runs a real vision pipeline:
   background subtraction (MOG2) for motion, contour analysis for
   object shape and size, HSV colour segmentation for stove-glow
   hazards, and centroid tracking across frames so the system follows
   one moving thing instead of reacting to every flicker.
2. **Decide (agent loop).** Detections become events with a risk
   score: motion in a watched zone, a person-like presence, an object
   left behind, a sustained stove glow, a fall-like collapse (a tall
   tracked shape suddenly becoming low and wide). Each event maps to
   an action tier: log, notify, or escalate.
3. **Act, then verify.** The agent does not fire and forget. After it
   acts, it re-observes: did the stove glow stop? Did the person get
   back up? Did anyone acknowledge the alert? Unacknowledged
   escalations stay open and visible instead of vanishing.
4. **Human in the loop.** A household member can mark any alert a
   false alarm. That feedback is logged and nudges the thresholds, so
   the system gets quieter about its own mistakes instead of louder.
   The agent never calls emergency services on its own — that line is
   deliberate and documented.

## Why this is an Agentic Vision entry, not a detector demo
The qualifying bar for the Agentic Vision path is that vision output
must change what the system does next. Hearthwatch clears it three
ways: a fall-like event changes the action tier (log becomes
escalate); a re-observation changes an open alert's state (resolved
vs still open); human feedback changes future thresholds. A chatbot
explaining a fixed picture would not qualify. This does.

## What it is NOT
- Not facial recognition. People are labelled only "person-like
  presence" from shape and motion. No identity, no templates, ever.
- Not a person classifier. The presence detector is a documented
  heuristic (tall, persistent, moving contour) with measured
  false-positive behaviour — not a claimed neural detector.
- Not a medical device. A "fall-like event" is a candidate signal for
  a human to check, not a diagnosis.
- Not a surveillance product. It runs on one household camera, stores
  no video by default, and keeps only event records (time, zone,
  event type, risk score).

## Evaluation, honestly
The test set is synthetic video generated with OpenCV itself (moving
rectangles, collapsing shapes, appearing boxes, glowing ellipses),
labelled frame by frame. Synthetic means controlled and reproducible —
and it means the numbers describe performance on staged scenes, not on
real homes. Both facts are stated in the report and in the film.
Failure cases (lighting-change false motion, small-pet-sized blobs,
occlusion) are measured and shown, not hidden.

## The AWS gap, stated up front
The competition requires a meaningful component on AWS. A standard
AWS account requires a credit card on file, which this project's
operator does not put on file anywhere. The code is container-ready
and ships with an ECS deployment sketch, but the live demo runs on a
free host instead, and the submission draft says so in plain words.
The one card-free AWS route — an AWS Educate Starter Account, which
needs no credit card — requires the entrant to apply and be approved,
which is a human step outside this build. If that account lands
before the deadline, the same container deploys to AWS unchanged.
