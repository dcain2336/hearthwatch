# AWS deployment sketch — NOT YET RUN

## Why this file exists instead of a live deployment
The competition requires a meaningful component on AWS. A standard
AWS account requires a credit card on file, and this project's
operator does not put a card on file anywhere — that is a standing
rule, not a preference. So no AWS account was created for this entry
and nothing below has been executed against AWS.

## The card-free route that would close the gap
An AWS Educate Starter Account requires no credit card (verified
against AWS Educate documentation, Oct 24, 2026). It is managed by a
third party (Vocareum), carries $30–$75 in capped credits, and limits
the available services. It requires the entrant to apply with a
student email and wait for approval — a human step with an unknown
timeline, outside this build's control. If that account lands, the
steps below deploy this same container unchanged.

## Deployment shape (when an AWS account exists)
1. Build the container: `docker build -t hearthwatch .`
2. Push to Amazon ECR in the account's region.
3. Run it as an Amazon ECS Fargate task (0.25 vCPU / 0.5 GB is
   enough — the pipeline is classical OpenCV on CPU, no GPU needed).
4. Put an Application Load Balancer in front of the task so the demo
   URL is a stable public endpoint for judges.
5. The demo serves the same single-page UI and `/api/run` endpoint;
   nothing in the code changes between local and AWS runs.

## What judges get instead, right now
- The live demo endpoint on a free host (see SUBMIT.md), running
  this exact code.
- This sketch, the Dockerfile, and the architecture diagram, so the
  AWS path is fully specified even though it is not yet executed.
- An honest statement in the submission: the AWS component is
  documented but not live, pending an account that requires no card
  (Educate) or a card the operator will not file.

## Cost note
Fargate at this size plus an ALB is a few dollars a month inside
free-tier/credit limits; the container itself is stateless and
stops when the task stops. No cost accrues while it is not running.
