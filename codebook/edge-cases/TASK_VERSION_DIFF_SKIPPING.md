# Task Version Diff Skipping

## Problem

When creating a task with `codebook task new`, files containing only version changes (like `codebook.version` updates) would create noise in the task output:

```diff
-Rendered by CodeBook [`v0.1.1-5-g8afa31a`](codebook:codebook.version)
+Rendered by CodeBook [`v0.1.1-5-g8afa31a`](codebook:codebook.version)
```

These diffs provide no useful information for the task.

## Solution

The task creation logic detects and skips version-only diffs:

```python
def is_version_only_diff(diff: str) -> bool:
    """Check if diff contains only codebook.version changes."""
```

### Detection Logic

A diff is considered "version-only" if:

1. All changed lines (starting with `+` or `-`) contain `codebook.version`
2. No other meaningful content was changed

### Example: Skipped

```diff
--- a/README.md
+++ b/README.md
@@ -1,3 +1,3 @@
-Rendered by CodeBook [`v0.1.1-5-g8afa31a`](codebook:codebook.version)
+Rendered by CodeBook [`v0.1.1-5-g8afa31a`](codebook:codebook.version)
```

This file would be **skipped** from the task.

### Example: Included

```diff
--- a/README.md
+++ b/README.md
@@ -1,5 +1,6 @@
 # My Project

+## New Section
+Added new content here.
+
-Rendered by CodeBook [`v0.1.1-5-g8afa31a`](codebook:codebook.version)
+Rendered by CodeBook [`v0.1.1-5-g8afa31a`](codebook:codebook.version)
```

This file would be **included** because it has non-version changes.

## CLI Behavior

When a file is skipped:
- No output for that file
- File count excludes skipped files
- Silent operation (no warning)

## Code Location

- `src/codebook/cli.py:task_new()` - Task creation command
- Detection happens during diff filtering

---

Rendered by CodeBook

--- BACKLINKS ---
[README](README.md "codebook:backlink")
