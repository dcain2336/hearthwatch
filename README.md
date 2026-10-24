# Hearthwatch — a home-safety vision agent

OpenCV AI Competition 2026 entry, Agentic Vision path.
OpenCV 5 perception + an agent loop where vision output changes what
the system does next (alert tiers, self-resolving alerts, feedback
learning). No facial recognition, ever. No autonomous emergency calls.

## Quick start

```bash
# Install pinned dependencies (OpenCV 5 is a competition requirement).
pip install --user --break-system-packages -r requirements.txt

# Build the synthetic test set (6 scenes, frame-labelled truth).
python3 src/make_testset.py evaluation/testset

# Score the pipeline (expect: 4/4 hits, 0 false positives).
python3 src/evaluate.py evaluation/testset

# Unit tests (expect: 8/8).
python3 tests/test_hearthwatch.py

# Demo server on http://127.0.0.1:8772/
python3 src/app.py 8772
```

## Layout

- `concept.md` — the idea, and the AWS gap stated up front.
- `src/sentinel.py` — OpenCV 5 perception (MOG2, contours, glow, tracking).
- `src/agent.py` — decision loop, tiers, verification, feedback learning.
- `src/app.py` — stdlib demo server + single-page UI.
- `src/make_testset.py` / `src/evaluate.py` — synthetic scenes + scorer.
- `tests/test_hearthwatch.py` — unit tests, no framework needed.
- `evaluation/testset/` — videos + manifest + results.
- `docs/REPORT.md` — the technical report (problem, architecture,
  implementation, evaluation, limitations, responsible use).
- `docs/architecture.svg` — architecture diagram (via make_diagram.py).
- `demo/` — gallery stills, narration, film build script, demo film.
- `aws-deploy/ECS-DEPLOY.md` — the AWS path, specified not executed.
- `Dockerfile` — container image (same code, deployable to ECS).

## The AWS gap, in one paragraph

The competition requires a meaningful component on AWS. A standard AWS
account requires a credit card on file, which this operator does not
file anywhere — so the AWS deployment is specified (ECS Fargate +
ALB, same container) but not executed. The card-free route is an AWS
Educate Starter Account (no card, capped credits), which needs the
entrant to apply and await approval. See `aws-deploy/ECS-DEPLOY.md`
and `docs/REPORT.md` section 6 for the full statement.
