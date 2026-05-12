# Session Handoff — MiniTorc Interview Prep

## Context
Sarthak is preparing for a Senior Software Engineer - Release Pipelines interview
at Torc Robotics in 2 days. Go slow, explain the why behind everything.

---

## What's Complete

### Day 1 — Bazel Monorepo (DONE)
- perception/, planner/, safety/ modules with BUILD files
- Dependency graph: perception → planner → safety
- Bazel query exercises (deps, rdeps, kind)
- Build stamping — git SHA embedded in version.py via genrule
- .bazelversion pinned to 6.5.0
- .gitignore, pushed to github.com/Sarthak-Rijal/minitorc

### Temporal Workflow (DONE — conceptual + running locally)
- Docker + Docker Compose running Temporal + PostgreSQL + UI
- activities.py, workflows.py, worker.py, trigger.py written
- Full workflow ran end to end (build → test → sign → approve → deploy)
- Deep conceptual understanding: durable execution, retry policies,
  signals, task queues, worker scaling, Temporal vs Step Functions

### Notes Written
- notes/bazel_01_fundamentals.md
- notes/bazel_02_query.md
- notes/bazel_03_build_stamping.md
- notes/bazel_04_remote_cache.md
- notes/temporal_concepts.md

---

## What's Next — 2 Days Remaining

### Day 3 — GitHub Actions (next session, start here)
Wire CI to automatically trigger the pipeline on git events.

Two workflow files to create:

**`.github/workflows/ci.yml`** — runs on every PR/push:
- Install Bazel (use .bazelversion)
- `bazel test //...`
- Block merge if tests fail

**`.github/workflows/release.yml`** — runs on tag push (`v*`):
- `bazel build //... --config=release`
- Package artifact: `tar -czf release-${GITHUB_SHA}.tar.gz bazel-bin/`
- Upload to S3: `aws s3 cp ...`
- Trigger Temporal: `python temporal/trigger.py --release-id ${GITHUB_SHA}`

Key concepts to explain to Sarthak:
- GitHub Actions triggers (on: push, pull_request, tags)
- How GITHUB_SHA connects to the digital thread
- OIDC authentication to AWS (no hardcoded credentials)
- How this wires Bazel + Temporal + S3 together

### Day 4 — Terraform + DynamoDB Audit Log
- S3 bucket for release artifacts (write: CI only, read: deployer)
- DynamoDB table: audit log (every pipeline event writes a record)
- IAM roles with least-privilege policies
- Add DynamoDB writes to Temporal activities (the digital thread)
- `terraform plan` before `terraform apply` — make this a habit

Key concepts to explain:
- IaC — plan before apply, always read the diff
- What + ~ - mean in terraform plan output
- Least-privilege IAM
- Why the audit log is the digital thread

### Day 5 — Polish + Interview Prep
- README that tells the story
- Practice the 5-minute demo script cold
- Debian packaging — conceptual only, 30 min read
  - What a .deb is, why it exists for embedded Linux
  - How genrule connects Bazel to dpkg-deb
- Remote cache hands-on with Docker (optional, 30 min)
  - docker run buchgr/bazel-remote-cache
  - Add --remote_cache to .bazelrc
  - bazel clean then build twice, see cache hits

---

## Sarthak's Strong Areas (don't over-explain)
- Remote cache vs artifact store distinction
- Strict dependency hygiene and why it matters
- Durable execution and retry policies
- Artifact promotion pipeline end-to-end
- Bazel query (deps, rdeps, kind)

## Areas to Reinforce
- Digital thread end-to-end answer — knows the pieces, needs to
  connect them into one fluent narrative
- Step Functions vs Temporal comparison — needs more confidence
- Build stamping internals — now understood after deep dive

---

## Repo State
- Branch: master
- Remote: git@github.com:Sarthak-Rijal/minitorc.git
- Last commit: fix: clean up BUILD files after Day 1 experiments
- Virtual env: .venv/ (run `source .venv/bin/activate` before Python)
- Temporal: running via docker compose in temporal/docker-compose.yml
  (PostgreSQL + Temporal server + UI at localhost:8080)

## Environment
- OS: Ubuntu Linux
- Bazel: 6.5.0 (via Bazelisk, pinned in .bazelversion)
- Python: 3.12.7
- Docker: 28.4.0

---

## How to Start Next Session
Tell Claude:
"Continue MiniTorc interview prep. Handoff doc is at
notes/handoff.md. Start with GitHub Actions CI/CD — Day 3."
