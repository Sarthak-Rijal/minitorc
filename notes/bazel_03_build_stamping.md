# Bazel 03 — Build Stamping

## What It Is

Build stamping embeds metadata (git SHA, timestamp) into build outputs at compile time.
Every artifact becomes traceable back to the exact commit it was built from.

---

## How It Works

Three pieces work together:

### 1. workspace_status_command script

A shell script Bazel runs before the build. Its output is captured as key-value pairs.

```bash
# scripts/workspace_status.sh
echo "STABLE_GIT_COMMIT $(git rev-parse HEAD)"
echo "BUILD_TIMESTAMP $(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

### 2. .bazelrc configuration

```ini
build:release --stamp
build:release --workspace_status_command=scripts/workspace_status.sh
```

`--stamp` tells Bazel to run the script and make values available to stamped targets.
Only active when you pass `--config=release`.

### 3. A stamped genrule target

```python
# version/BUILD
genrule(
    name = "version",
    outs = ["version.py"],
    stamp = True,
    cmd = """
        commit=$$(grep ^STABLE_GIT_COMMIT bazel-out/stable-status.txt | awk '{print $$2}');
        timestamp=$$(grep ^BUILD_TIMESTAMP bazel-out/volatile-status.txt | awk '{print $$2}');
        echo "GIT_COMMIT = '$$commit'" > $@
        echo "BUILD_TIMESTAMP = '$$timestamp'" >> $@
    """,
    visibility = ["//visibility:public"],
)
```

---

## STABLE_ vs volatile keys

The `STABLE_` prefix determines how Bazel treats cache invalidation:

**`STABLE_GIT_COMMIT`** — written to `bazel-out/stable-status.txt`
When this value changes (new commit), Bazel invalidates the cache for all stamped targets
and rebuilds them. Changing commits = new build, guaranteed.

**`BUILD_TIMESTAMP`** — written to `bazel-out/volatile-status.txt`
Changes every build but does NOT invalidate the cache. You get a fresh timestamp
in the output without forcing an unnecessary rebuild of everything.

---

## Why $$ instead of $ in genrule cmd

In Bazel genrule `cmd`, a single `$` is reserved for Make variables (`$(SRCS)`, `$@`, etc.).
To write a real shell `$` (like `$commit` for a shell variable), you write `$$`.
Bazel strips one `$` before passing the command to the shell.

```python
cmd = """
    commit=$$(grep ...)    # $$commit becomes $commit in the shell
    echo "$$commit" > $@   # $@ is a Make variable — Bazel replaces with the output path
"""
```

---

## Why not $(STABLE_GIT_COMMIT) directly?

This is a common mistake. `$(VAR)` in genrule cmd is Make variable syntax.
Workspace status values are NOT Make variables — Bazel writes them to files instead.
You read those files with `grep` in the cmd.

---

## Result

```bash
bazel build //version:version --config=release
cat bazel-bin/version/version.py
```

```python
GIT_COMMIT = 'e727b7b784617fa9783c4cc344f42d368af3b344'
BUILD_TIMESTAMP = '2026-05-11T18:31:58Z'
```

Make a commit, rebuild — the SHA changes. The artifact knows what code it is.

---

## genrule

The escape hatch for when no existing rule fits. Lets you run an arbitrary shell
command as a Bazel build action.

```python
genrule(
    name = "my_output",
    srcs = ["input.txt"],       # input files
    outs = ["output.txt"],      # declared outputs — Bazel tracks these
    cmd = "cat $(SRCS) > $@",   # shell command to produce the outputs
)
```

`$(SRCS)` and `$@` are Make variables Bazel expands before running the command.
Anything more complex than a shell one-liner should be a proper rule instead.
