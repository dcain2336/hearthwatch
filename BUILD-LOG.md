# Hearthwatch — build log (Sat Oct 24, 2026, single-day build)

## Hour 0 — Live verification (contest_ops_hygiene)
- Official page https://opencv26.devpost.com/ read live: finals due
  Oct 26, 2026, 11:59 PM PT = Oct 27, 2026, 02:59 AM EDT (matches the
  overnight scout). Prize pool $20,250 confirmed ($5k/$3k/$2k + 2x$1k
  specials + 55x$150 grants on the main page; rules page lists the
  $12,000 cash prizes).
- Submission bar confirmed: technical report, code repo, pinned deps
  + build/test instructions, architecture diagram, working endpoint
  OR live screen-share demo, ≤5-min video, evaluation evidence.
- Eligibility: age 13+, no government-affiliation exclusion, no
  residency exclusion in the published rules. Only exclusion: people
  directly administering/judging. Scott clears it.
- AWS crux found in hour 0 and reported up the chain: a standard AWS
  account requires a card on file (standing rule: never file one).
  Card-free route verified live: AWS Educate Starter Account needs
  no card but requires the entrant's own application + approval
  (unknown timeline). Decision: build the real entry now, ship the
  AWS path as specified-not-executed, state it everywhere.

## Environment
- opencv-python 5.0.0.93 + numpy 2.5.4 installed (PEP 668 needed
  --break-system-packages, per the sgp4 lesson). ffmpeg present.
- OpenCV 5.0 headless wheel: no HOGDescriptor, no CascadeClassifier
  exposed — pipeline designed around what IS present (MOG2, KNN,
  contours, SimpleBlobDetector, QRCodeDetector). Presence is a
  documented contour heuristic, never claimed as a neural detector.

## Build order
1. concept.md (incl. the AWS gap up front).
2. src/sentinel.py — perception pipeline, every line commented.
3. src/agent.py — tiers, streaks, verification, feedback learning.
4. src/make_testset.py + src/evaluate.py — 6 synthetic scenes.
5. First eval: 3/4 hits, 0 FP — fall scene MISSED.
   Root cause (debugged frame by frame): motion blobs show only the
   changed region during a collapse, not the true shape; and the
   original fall scene had the walker present from frame 1, so no
   clean reference existed. Fix: merged motion + frozen-reference
   boxes for tracking (true shapes), and all scenes rebuilt with a
   35-frame empty lead-in so the frame-31 reference is an empty room.
   Second eval: 4/4 hits, 0 FP.
6. Cross-talk fixes, each principled and documented: fallen bodies
   excluded from left-object (explained by the fall); stove-zone
   boxes excluded from left-object (explained by glow). One
   regression caught and fixed the same way: the package scene's box
   sat inside the default stove zone, so the scene was restaged
   (box on the left, stove bottom-right) and the suite returned to
   4/4, 0 FP.
7. Unit tests 8/8. Demo server verified live (scene list + fall run
   + annotated video). Server stopped after verification.
8. Gallery stills (4 annotated frames) + film: 8 narration segments
   via TTS, annotated clips + cards, 2:35 total (cap is 5:00).
   One build failure caught: segment-2 used image-loop syntax on a
   video input and a relative-path concat resolution produced a
   6-second film of only the title card. Fixed (stream_loop +
   absolute concat paths), rebuilt, verified duration 155s and
   spot-checked frames (bright clip frame, dark card frame).
9. Docs: REPORT.md, architecture.svg (generated), README.md,
   SUBMIT.md, SUBMISSION-DRAFT.md, Dockerfile, ECS-DEPLOY.md.

## Final verified numbers (re-run at the end of the build)
- Evaluation: 4/4 event scenes HIT, 0 false positives, recall 1.00.
- Latencies: walk 10, fall 4, package -10 (early: box static since
  frame 85, window starts at fully-alone frame 145), stove 5 frames.
- Unit tests: 8/8.
- Film: 2:35, h264 + aac, all 8 segments present.

## Not done (parent's steps, per assignment)
- Repo push via PAT route.
- Demo endpoint hosting on a free host (or live screen-share fallback).
- Film upload to the personal YouTube channel, unlisted.
- Devpost submission with SUBMISSION-DRAFT.md (fill the 3 TODO links).
- AWS Educate Starter Account application (Scott's human step, if he
  wants the AWS component live before judging).
- On-camera presenter segment for the film ("shows the team") —
  entrant's call; film as built shows no face.
