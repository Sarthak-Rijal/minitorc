# Bazel 01 — Fundamentals

## The Problem Bazel Solves

In a large codebase, changing one file should only rebuild what's affected.
Without Bazel: run everything, slow, non-reproducible, hidden dependencies.
With Bazel: explicit dependency graph — only affected targets rebuild, undeclared dependencies are impossible.

---

## Hermeticity

Builds are isolated from the host environment. Same inputs always produce the same outputs,
regardless of what's installed on the machine.

- No hidden dependency on system Python, system libraries, or environment variables
- Two engineers on different machines get identical binaries from the same source

---

## WORKSPACE

The root of the Bazel universe. Every `//` path in the repo is relative to the
directory containing WORKSPACE.

```python
workspace(name = "minitorc")

http_archive(
    name = "rules_python",
    sha256 = "9d04041...",        # cryptographic fingerprint of the downloaded file
    strip_prefix = "rules_python-0.26.0",
    url = "https://github.com/.../rules_python-0.26.0.tar.gz",
)

load("@rules_python//python:repositories.bzl", "py_repositories")
py_repositories()
```

**`http_archive`** — downloads an external dependency as a `.tar.gz`, verifies it with SHA256,
and makes it available as `@rules_python` throughout the workspace.

**`sha256`** — Bazel downloads the file, hashes it, compares. Mismatch = hard fail.
Without it: different engineers could silently pull different bytes from the same URL.

**`strip_prefix`** — removes the outer folder from the archive so paths start cleanly.
Without it: `@rules_python//rules_python-0.26.0/python/...` — extra folder in the way.

**`py_repositories()`** — registers the Python interpreter and toolchain with Bazel.
Separate from the rules themselves. Without it, Bazel doesn't know how to invoke Python.

**The pattern for every external dep:**
`http_archive` to download → `load` to import init functions → call those functions to activate.

---

## .bazelversion

Pins the exact Bazel version for the entire team. Bazelisk reads this and downloads
the right version automatically.

```
6.5.0
```

Without it: Bazelisk downloads the latest version. Engineers on different machines
or at different times get different Bazel versions. BUILD files that work on one
version silently break on another — this is exactly what happened on Day 1 with Bazel 9.

---

## BUILD Files

Every directory can have a BUILD file declaring **targets** — named buildable units.

```python
py_library(
    name = "detector",                     # referenced as //perception:detector
    srcs = ["detector.py"],                # files that BELONG to this target
    deps = ["//perception:detector"],      # other targets this needs to compile
    visibility = ["//visibility:public"],  # who is allowed to depend on this
)

py_test(
    name = "detector_test",
    srcs = ["detector_test.py"],
    deps = [":detector"],                  # :detector = same package shorthand
)
```

### srcs vs deps

- `srcs` — source files in this directory that ARE this target
- `deps` — other already-built targets that must exist before this compiles
- Rule: if you import it in code → `deps`. If it's a file you own → `srcs`

### py_library vs py_test

`py_library` — builds an artifact, nothing executes. Meant to be depended on by other targets.

`py_test` — builds AND executes. Bazel checks exit code (0 = pass). Gets special behavior:
`--test_output`, `--test_filter`, parallel execution, cached test results.

Using `py_test` for libraries would cause Bazel to try to run them as binaries.
Using `py_library` for tests means `bazel test //...` never finds or runs them.

### Visibility

Controls who can declare a dependency on this target.

```python
visibility = ["//visibility:public"]     # anyone in the repo
visibility = ["//safety:__pkg__"]        # only the safety/ package
visibility = ["//visibility:private"]    # nobody outside this BUILD file
```

Tests don't need visibility — nothing ever depends on a test target.

### Target Addressing

```
//perception:detector
  ^^^^^^^^^^  ^^^^^^^^
  package     target name
  (directory) (name = "..." in BUILD)
```

- `//perception:detector` — absolute path from workspace root
- `:detector` — relative, same package (same BUILD file)

---

## Dependency Graph

Bazel reads all BUILD files, builds a directed acyclic graph (DAG), determines build order.
Circular dependencies fail immediately at analysis time — before any code compiles.

```
perception  <── planner  <── safety
```

Change `perception/detector.py`:
- Bazel rebuilds perception, planner, safety (all downstream)
- Unrelated modules — skipped entirely

### Strict Dependency Hygiene

Bazel builds the full transitive graph but only allows you to USE what you explicitly
declare in your own `deps`.

If `safety` imports from `perception.detector` directly in code, it must declare
`//perception:detector` in its own `deps` — even though `planner` already depends on it.

Why: if `planner` later removes its perception dep, `safety`'s build breaks immediately
and forces an explicit decision. Without strict deps, the breakage is silent.

---

## Starlark (BUILD file language)

Python-like but deliberately restricted. No `import`, no file I/O, no classes.
BUILD files must be deterministic — side effects break reproducibility.

`print()` is allowed but fires on every analysis phase, not just during builds.
Don't use it in BUILD files — it produces noise on every `bazel build` command.

Same rule structure for all languages — only names change:
```python
cc_library(name = "...", srcs = [...], deps = [...])   # C++
java_library(name = "...", srcs = [...], deps = [...])  # Java
py_library(name = "...", srcs = [...], deps = [...])    # Python
```

---

## Rule Types — Bazel 6 vs 7+

In Bazel 6: `py_library`, `py_test`, `py_binary` are native built-ins, no load needed.

In Bazel 7+: moved to `rules_python`, must be loaded explicitly:
```python
load("@rules_python//python:defs.bzl", "py_library", "py_test")
```

`cc_library`, `cc_test` remain native built-ins in all versions.
Go rules (`go_library`, `go_test`) were never built-in — always required `rules_go`.

---

## Build Outputs

`bazel-bin/` is a symlink pointing into `~/.cache/bazel/`.

Build configurations stored separately so they don't overwrite each other:
- `k8-fastbuild` — default, unoptimized (standard `bazel build //...`)
- `k8-opt` — optimized (`--config=release`)
- `k8-dbg` — debug symbols included

Each target's outputs mirror the source tree:
```
bazel-bin/
  perception/
    detector_test              <- runnable test binary
    detector_test.runfiles/    <- hermetic sandbox with only declared files
      MANIFEST                 <- map of every file the test is allowed to see
```

The `MANIFEST` file is hermeticity at execution time — the test can only access
files that were explicitly declared in `srcs` and `deps`.
