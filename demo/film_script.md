# Hearthwatch demo film — narration script (all values are real)

## Segment 1 — Title (card, 12s)
"Hearthwatch. A home-safety vision agent for the OpenCV AI Competition,
on the Agentic Vision path."

## Segment 2 — Problem (empty-room still, 30s)
"A camera watches a home, but nobody watches the camera. A fall, a stove
left glowing, or a package left at the door is only noticed when it is
already too late. Hearthwatch turns that camera into an agent that
perceives, decides, acts — and then checks its own work."

## Segment 3 — Presence (walk clip, 45s)
"First, perception, built on OpenCV 5. Background subtraction finds
motion. Contours measure shape and size. Centroid tracking follows one
moving thing across frames instead of reacting to every flicker. Here, a
tall, persistent shape becomes a person-like presence — logged, not
alarmed. No facial recognition: people are presence only, never identity."

## Segment 4 — Fall (fall clip, 60s)
"Now the agent loop. A tracked tall shape suddenly goes low and wide.
That is a fall-like candidate, and vision output changes what the system
does next: a routine log becomes an escalation, an urgent alert that
stays open until a human acknowledges it. Not a diagnosis — a signal for
a human to check."

## Segment 5 — Package and stove (package + stove clips, 60s)
"Two more events. A small box appears, sits still, and stays after the
walker leaves: a left object, a notification, not an emergency. And a
sustained orange-red glow in the stove zone: a stove alert, but only
after five consecutive frames — one bright frame could be a reflection.
When the glow clears, the agent re-observes and resolves its own alert.
That verification step is the difference between a detector and an agent."

## Segment 6 — Feedback (card, 45s)
"And the household trains it back. Mark any alert a false alarm, and the
thresholds nudge upward — bounded, so feedback can quiet the system but
never silence it. The agent never calls emergency services on its own.
That line is deliberate."

## Segment 7 — Results and honesty (card, 45s)
"Measured on six synthetic scenes, drawn with OpenCV and labelled frame
by frame: four out of four event scenes detected, zero false positives
on the empty room and the lighting-change scene. Detection latencies of
four to fifteen frames at ten frames per second. Synthetic means
controlled and reproducible — and it means these numbers describe staged
scenes, not real homes. Both facts matter, so both are stated."

## Segment 8 — AWS honesty + close (card, 15s)
"One gap, stated plainly: the competition requires a component on AWS,
and this demo runs on a free host instead, because a standard AWS
account requires a card on file. The code is container-ready, and the
AWS deployment is fully specified. Hearthwatch: see, decide, act, verify."
