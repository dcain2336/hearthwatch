# Devpost submission draft — Hearthwatch (paste-ready; two TODO slots)

## Project name
Hearthwatch — a home-safety vision agent

## Tagline
A camera watches a home, but nobody watches the camera. Hearthwatch
turns that camera into an agent that perceives, decides, acts — and
then checks its own work.

## Inspiration
Household cameras record everything and notice nothing. A fall, a
stove left glowing, a package at the door — each is visible on
camera long before anyone acts on it. We wanted the camera itself to
close that gap, with an agent whose decisions are driven by what it
sees, not by a fixed script.

## What it does
Hearthwatch watches one household camera with an OpenCV 5 pipeline
(MOG2 motion, contour shape analysis, stove-glow colour detection,
centroid tracking) and an agent loop on top. Detections become events
with action tiers: person-like presence is logged, a left-behind
object or a sustained stove glow notifies, and a fall-like collapse
escalates to an urgent alert that stays open until a human
acknowledges it. Then the agent verifies itself: when the glow
clears, it resolves its own stove alert from fresh frames. And the
household trains it back — marking an alert a false alarm nudges the
thresholds, bounded so feedback can quiet the system but never
silence it. The agent never calls emergency services on its own, and
it never does facial recognition: people are presence only, never
identity.

## How we built it
Python with OpenCV 5.0.0 (pinned) and the standard library only —
no web framework, no neural model. The perception pipeline is
classical computer vision by design: explainable, CPU-runnable, and
measurable. The demo server is a single-page UI that runs any test
scene through the pipeline and shows the annotated video, the events,
and the open alerts with working acknowledge / false-alarm buttons.
The code is containerised with a Dockerfile for deployment.

## Challenges we ran into
Two honest ones. First, a fall is invisible to a motion-only tracker:
a collapsing shape overlaps its own previous position, so the motion
blob shows only the changed region, not the person's true shape. The
fix was merging motion boxes with boxes from a frozen reference
frame, so tracks follow true shapes. Second, one detector's output
is another's false positive: a fallen body is short and still, so it
also trips the left-object detector, and a stove glow patch does too.
Both are now suppressed by explanation — a box already explained by
a fall or by the stove zone is not reported twice.

## Accomplishments that we're proud of
On six synthetic scenes (drawn with OpenCV, frame-labelled ground
truth): four out of four event scenes detected, zero false positives
on the empty room and on a global lighting-change scene, detection
latencies of four to fifteen frames at ten frames per second. Eight
unit tests pass. The film demonstrates every event class live.

## What we learned
An agent is not a detector with a notification attached. The moment
the system re-observes its own alerts and lets human feedback change
its future behaviour, the whole character of the product changes —
from something that cries wolf to something that can be trusted to
stay quiet until it matters.

## What's next for Hearthwatch
Real-home validation (the current numbers describe staged scenes, not
real rooms), per-deployment zone configuration, and the AWS
deployment below.

## AWS deployment — stated plainly
This entry's AWS component is documented but not yet live. A
standard AWS account requires a credit card on file, which the
entrant does not put on file. The deployment is fully specified
(ECS Fargate + Application Load Balancer, same container, Dockerfile
in the repo). The card-free route — an AWS Educate Starter Account,
which requires no credit card — is pending the entrant's application
and approval; if it lands before judging, the same container
deploys to AWS unchanged.

## Built with
OpenCV 5, Python (standard library), NumPy, ffmpeg

## Links (TODO — parent fills at submit time)
- Demo video (unlisted, personal channel): TODO
- Code repository: TODO
- Live demo endpoint: TODO (free host; see SUBMIT.md)
