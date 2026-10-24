# SUBMIT.md — Hearthwatch submission checklist (for the parent agent)

## Competition
OpenCV AI Competition 2026, powered by AWS — Devpost:
https://opencv26.devpost.com/
Deadline (verified live Oct 24, 2026): **Mon Oct 26, 2026, 11:59 PM
Pacific Time = Tue Oct 27, 2026, 02:59 AM EDT.**

## What the submission needs (per the official page, verified live)
- [ ] Technical report — `docs/REPORT.md` (DONE)
- [ ] Code repository, public or judge-accessible — push this folder
      via the PAT route (parent step, NOT done by the build agent)
- [ ] Pinned dependencies + build/test instructions — `requirements.txt`
      + README.md (DONE)
- [ ] Architecture diagram — `docs/architecture.svg` (DONE)
- [ ] Working web endpoint OR arranged live screen-share demo —
      endpoint: host the demo server on a free host (Render/Cloudflare;
      parent step). Fallback honestly available: live screen-share.
- [ ] Video ≤ 5 minutes — `demo/hearthwatch-demo.mp4`, 2:35 (DONE);
      upload to the personal YouTube channel, unlisted (parent step)
- [ ] Evaluation evidence incl. failure cases — `docs/REPORT.md`
      section 5 + 7, `evaluation/testset/results.json` (DONE)

## Path
Agentic Vision Award path (agent loop: vision output changes later
decisions — tier escalation, self-resolving alerts, feedback
learning). COOL path NOT pursued (needs AWS Graviton + Marketplace
COOL; no AWS account — see below).

## The AWS statement (must stay in the submission text)
The submission draft states plainly that the AWS component is
documented but not live, because a standard AWS account requires a
card on file and the operator does not file cards. Do NOT soften or
remove this. If an AWS Educate Starter Account (no card) is approved
before the deadline, deploy the container to ECS per
`aws-deploy/ECS-DEPLOY.md` and update the draft to say so.

## Film note
The film is screen-recorded narration with no on-camera presenter.
The rules ask the video to show "the team" — the parent/entrant
decides whether to add an on-camera intro. The film as built does
not show any person's face.

## Do NOT do
- Do not claim a live AWS deployment exists.
- Do not claim the synthetic evaluation describes real homes.
- Do not describe presence detection as a person classifier or a
  neural detector. It is a documented contour heuristic.
- Do not submit with any EOD/tactical/combat content (none exists
  in this entry).
