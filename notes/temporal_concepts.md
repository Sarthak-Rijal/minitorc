# Temporal — Core Concepts

## What Problem Temporal Solves

Long-running release pipelines (hours) cannot afford to restart from zero
because a server hiccuped. A cron job or task queue loses state on failure.
Temporal persists every event to a database so workflows survive anything —
worker crashes, server reboots, spot instance terminations.

---

## The Four Files

```
activities.py  ← the actual work (build, test, sign, approve, deploy)
workflows.py   ← the coordinator (calls activities in order, handles signals)
worker.py      ← the process that runs everything, connects to Temporal
trigger.py     ← CLI to kick off a new workflow
```

---

## Activities

Each activity is one unit of work. Plain async Python function with `@activity.defn`.

```python
@activity.defn
async def build_components(release_id: str) -> str:
    # does real work
    return "artifact.tar.gz"
```

- Independent — doesn't know about other activities or the workflow
- Can fail and be retried — Temporal handles this automatically
- Sends heartbeats for long-running work so Temporal knows it's alive
- If it raises an exception, Temporal retries per the retry policy

---

## Workflows

The coordinator. Calls activities in sequence. Does NOT do real work itself.

```python
@workflow.defn
class ReleaseWorkflow:

    @workflow.signal
    async def approve(self):
        self._approved = True          # unblocks await_human_approval

    @workflow.run
    async def run(self, release_id: str):
        await workflow.execute_activity(build_components, ...)
        await workflow.execute_activity(run_integration_tests, ...)
        await workflow.execute_activity(sign_artifact, ...)
        await workflow.wait_condition(lambda: self._approved)  # blocks until signal
        await workflow.execute_activity(deploy_to_truck, ...)
```

Workflows must be deterministic — no random numbers, no system calls, no network
calls, no current time. Temporal replays the event history to reconstruct state
after a crash. Non-deterministic code produces different results on replay and
causes a mismatch error.

---

## Signals

A message sent from outside into a running workflow.

```python
# Send approval signal from CLI or dashboard
handle = client.get_workflow_handle('release-001')
await handle.signal('approve')
```

The workflow is paused at `wait_condition`. When the signal arrives, Temporal
delivers it, `_approved` becomes True, and the workflow resumes. No polling.
No sleep loop. Temporal suspends the workflow until the signal comes in.

---

## Retry Policy

```python
retry_policy = RetryPolicy(
    maximum_attempts=3,          # try 3 times total before permanently failing
    initial_interval=timedelta(seconds=1),  # wait 1s before first retry
    backoff_coefficient=2.0,     # each wait doubles: 1s → 2s → 4s
)
```

**`maximum_attempts`** — how many total attempts before the activity is marked failed.
A genuine flake passes on attempt 2. Broken code exhausts all attempts and fails the workflow.

**`initial_interval`** — how long to wait before the first retry. Gives transient
failures (resource contention, network blip) time to clear.

**`backoff_coefficient`** — exponential backoff. Each retry waits longer than the
previous. Prevents hammering a struggling system with immediate retries.

---

## Task Queues

Routing mechanism — not a rate limiter. Multiple workers listen on the same queue
and pick up tasks in parallel.

```python
# worker.py
Worker(client, task_queue="release-queue", ...)

# workflows.py
workflow.execute_activity(build_components, task_queue="build-queue", ...)
```

Different queues route work to different worker fleets:
```
release-queue  → standard workers
build-queue    → high-CPU workers (heavy compilation)
approval-queue → lightweight workers (just polls for signals)
```

Each fleet sized independently based on what it actually does.

---

## Durable Execution — How It Works

Temporal doesn't save a snapshot of your program. It persists an append-only
event log to PostgreSQL:

```
event 1: WorkflowStarted        (release-001)
event 2: ActivityScheduled      (build_components)
event 3: ActivityCompleted      (build_components → "artifact.tar.gz")
event 4: ActivityScheduled      (run_integration_tests)
event 5: ActivityFailed         (run_integration_tests → RuntimeError)
event 6: ActivityScheduled      (run_integration_tests retry 2)
event 7: ActivityCompleted      (run_integration_tests → "tests_passed")
...
```

When a worker restarts after a crash, Temporal replays this log — not by
re-running the activities, but by fast-forwarding through recorded history.
The worker arrives at the last incomplete step and resumes from there.

---

## Infrastructure Failure vs Code Failure

**Infrastructure failure** (worker crashes, spot instance terminated):
→ Temporal resumes the same workflow from the last completed activity.
→ Kubernetes restarts the worker pod automatically.
→ No human intervention needed.

**Code failure** (tests fail because the code is broken):
→ Retry policy exhausts all attempts.
→ Workflow marked FAILED permanently.
→ Artifact stays in candidates/, never promoted to live/.
→ Engineer fixes code, new commit, new workflow.

**Flaky test** (randomly fails):
→ Temporal retries automatically.
→ Same workflow continues if a retry passes.

---

## Workers at Scale

Worker code is identical locally and in production. Scale is controlled by
Kubernetes replicas:

```yaml
spec:
  replicas: 10    # 10 copies of worker.py running simultaneously
```

Temporal distributes tasks across all workers via polling. Ten workflows run
in parallel with zero code changes. Kubernetes HorizontalPodAutoscaler scales
the fleet up when queue depth rises, down when idle.

---

## Temporal vs AWS Step Functions

| | Temporal | Step Functions |
|---|---|---|
| Defined in | Python code | JSON/YAML config |
| Testable | Yes — unit test the workflow | No — can't test config |
| Cost | Fixed infrastructure | Per state transition |
| Execution model | Durable — survives crashes | State machine — loses context on failure |
| Expressiveness | Full Python — conditions, loops, signals | Limited state machine constructs |

For complex release pipelines with conditional logic, human approval gates,
and artifact signing — code is more expressive and testable than config.

---

## Why Not a Cron Job or Task Queue

**Cron job** — fires once, no state. If it crashes halfway, it either runs again
from the beginning or doesn't run again at all. No resume.

**Celery/SQS** — task queue handles retries but has no concept of a multi-step
workflow. Each task is independent. No built-in way to say "only run step 3
after step 2 completes successfully."

**Temporal** — durable multi-step workflow with retries, signals, timeouts,
and crash recovery built in. The workflow is the unit, not the individual task.

---

## The Release Pipeline Flow

```
Engineer merges PR
        │
GitHub Actions: bazel build --config=release
        │
CI packages: tar -czf release-{sha}.tar.gz bazel-bin/
        │
CI uploads: s3://candidates/{sha}/release-{sha}.tar.gz
        │
CI calls: python trigger.py --release-id {sha}
        │
Temporal ReleaseWorkflow:
  build_components       verify build is clean
  run_integration_tests  full system tests (retries on flake)
  sign_artifact          cryptographic signature
  await_human_approval   blocks until approve signal received
  deploy_to_truck        promotes artifact to s3://live/v1.x/
        │
Other teams pin WORKSPACE sha256 to new version
```
