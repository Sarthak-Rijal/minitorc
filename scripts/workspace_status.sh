#!/bin/bash
# Bazel runs this script and captures the output as key-value pairs.
# Keys prefixed with STABLE_ trigger rebuilds when their value changes.
# Keys without STABLE_ are volatile — they change every build but don't force rebuilds.

echo "STABLE_GIT_COMMIT $(git rev-parse HEAD 2>/dev/null || echo 'unknown')"
echo "STABLE_GIT_STATUS $(git status --porcelain | wc -l | tr -d ' ' | xargs -I{} echo {} files changed 2>/dev/null || echo 'unknown')"
echo "BUILD_TIMESTAMP $(date -u +%Y-%m-%dT%H:%M:%SZ)"
