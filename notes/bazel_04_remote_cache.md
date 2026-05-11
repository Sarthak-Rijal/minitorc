# Bazel 04 — Remote Cache

## The Problem

Local disk cache only helps the machine that built it. On a team of 50 engineers,
every developer's machine builds from scratch even if CI built and tested the same
targets an hour ago.

---

## What the Remote Cache Is

A shared key-value store hosted on a server:

```
Key:   SHA256 hash of (all input files + build command + toolchain + flags)
Value: the output files that resulted from that action
```

When Bazel needs to build an action, it checks in order:
1. Local memory cache
2. Local disk cache
3. Remote cache (network round trip)
4. Actually compile — only if all three miss

---

## How It Fits the Team

```
┌─────────────────────────────────────────┐
│           REMOTE CACHE SERVER           │
│         (bazel-remote on S3/GCS)        │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴───────┐
       │               │
  CI Runner        CI Runner
  (writes)         (writes)
       │
  Engineers read — never write
  Sarthak / Ahmed / Priya ...
```

CI builds first, writes to the cache. Developers run later, get cache hits.
Developers are read-only — they cannot pollute the cache with unverified outputs.

---

## .bazelrc Configuration

```ini
# Committed to the repo — everyone gets this automatically on clone

# Everyone reads from the remote cache
build --remote_cache=grpc://cache.company.com:9090

# Developers cannot write to it
build --remote_upload_local_results=false
```

```ini
# .bazelrc.ci — used only on CI runners

# CI can write
build --remote_upload_local_results=true
build --google_credentials=/secrets/ci-service-account.json
```

Developer runs `bazel build //...` — automatically reads from remote cache.
No setup required on the developer's machine. Config ships with the repo.

---

## Remote Cache vs Artifact Store

Two separate systems that look similar but serve different purposes:

| | Remote Cache | Artifact Store (S3) |
|---|---|---|
| Purpose | Speed | Reliability + Traceability |
| Stores | Intermediate compiled outputs | Versioned release artifacts |
| Key | Content hash of inputs | Version + git SHA |
| Lifetime | Temporary, evictable | Permanent, immutable |
| Who writes | CI only | Release pipeline after gates pass |
| Who reads | Everyone (developers + CI) | Deployment systems + other teams |

The remote cache makes builds fast. The artifact store makes releases trustworthy.

---

## What Actually Runs the Server

Most common options:

| Tool | What it is |
|---|---|
| `bazel-remote` | Open source Go binary, self-hosted, S3 backend |
| BuildBuddy | SaaS, free tier available |
| Google Cloud Build | Managed, GCS backend |

All speak the same protocol (REAPI). Switching is one line in `.bazelrc`.

---

## Artifact Promotion Pipeline

```
Developer commits
       |
CI: bazel build + test --> remote cache written (automatic)
       | tests pass
       v
Package artifact --------> s3://candidates/<git-sha>/
       |
Temporal ReleaseWorkflow:
  run_integration_tests
  sign_artifact
  await_human_approval    <- promotion gate
  deploy_to_truck ---------> s3://live/v1.4.2/  (immutable)
       |
Other teams pin WORKSPACE sha256 to new version
```

Nothing reaches live without passing all gates.
Other teams never point at "latest" — they pin to an exact SHA256.

---

## Hands-On (upcoming)

Run `bazel-remote` locally via Docker:

```bash
docker run --rm -p 9090:9090 buchgr/bazel-remote-cache \
  --max_size=5
```

Add to `.bazelrc`:
```ini
build --remote_cache=grpc://localhost:9090
```

Run `bazel clean` then `bazel build //...` twice.
First run: cache miss, compiles everything, uploads to bazel-remote.
Second run: full cache hit, downloads instead of compiling.
