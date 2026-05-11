# Bazel 02 — Query

## What Bazel Query Does

Interrogates the dependency graph without building anything. Useful for understanding
blast radius before making a change, discovering all targets of a type, and debugging
unexpected build failures.

---

## Core Commands

```bash
# What does safety depend on? (forward — what it needs to build)
bazel query 'deps(//safety:validator)'

# What depends on perception? (reverse — what breaks if perception changes)
bazel query 'rdeps(//..., //perception:detector)'

# All test targets in the repo
bazel query 'kind(py_test, //...)'

# All targets in a single package
bazel query '//perception:*'

# Tests affected by a specific target (used in CI for targeted runs)
bazel query 'kind(py_test, rdeps(//..., //perception:detector))'
```

---

## deps vs rdeps

```
perception  <── planner  <── safety
```

`deps(//safety:validator)` — follow arrows forward:
returns `planner`, `perception` (everything safety needs)

`rdeps(//..., //perception:detector)` — follow arrows backward:
returns `planner`, `safety` (everything that would break if perception changed)

The `//...` in rdeps is the universe to search within — "look across the whole repo
for anything that depends on perception."

---

## kind

Filters results by rule type.

```bash
bazel query 'kind(py_test, //...)'
```

Without `kind`: returns everything — libraries, tests, genrules.
With `kind(py_test, //...)`: returns only targets whose rule is `py_test`.

Other useful kinds: `py_library`, `cc_binary`, `genrule`.

---

## Targeted Test Selection in CI

Instead of running the full test suite on every PR:

```bash
# Find only the tests affected by a change to perception
bazel query 'kind(py_test, rdeps(//..., //perception:detector))'

# Pipe directly into bazel test
bazel test $(bazel query 'kind(py_test, rdeps(//..., //perception:detector))')
```

On a 200-module repo, changing one file might affect 3 test targets.
Running 3 tests instead of 200 is the difference between a 2-minute and 18-minute CI run.

---

## Common Error

```
ERROR: no such target '//perception:perception'
Tip: use `query "//perception:*"` to see all targets in that package
```

This means you guessed the target name wrong. Use `//perception:*` to list
what's actually declared in that package's BUILD file.
