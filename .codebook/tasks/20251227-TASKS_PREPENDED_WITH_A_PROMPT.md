# Tasks Prepended With A Prompt

## 1. .codebook/TASKS.md

### Before

```markdown
# Task Management

CodeBook includes a task management feature for capturing documentation changes.

## Creating a Task

```bash
codebook task new "Title of the task" ./scope
```

This creates `.codebook/tasks/YYYYMMDD-TITLE_OF_THE_TASK.md` containing:
- Current content of each modified file
- Git diff showing changes from HEAD

Users can delete the tasks by running `codebook task delete` with the "Title of the task" or without it the pick tool will be used to select the task to delete from the list of tasks.


## Behavior

By default, `task new` only includes files that have uncommitted changes (staged or unstaged). Use `--all` to capture all files regardless of git status.

The title is converted to `UPPER_SNAKE_CASE` for the filename.
And the task is prepended with a generic wrapper describing what to be changed.
This wrapper can be customized by the user by adding -prefix and -suffix to `codebook.yml`

## Examples

### Capture modified docs

```bash
codebook task new "API Documentation Update" ./docs
```

Creates `.codebook/tasks/API_DOCUMENTATION_UPDATE.md` with only the modified markdown files in `./docs`.

### Capture a single file

```bash
codebook task new "README Changes" ./README.md
```

### Capture all files (snapshot)

```bash
codebook task new "Full Docs Snapshot" ./docs --all
```

## Output Format

```markdown
# Title of the task

## 1. path/to/file.md

### Before

\`\`\`markdown
Current file content...
\`\`\`

### Diff

\`\`\`diff
diff --git a/path/to/file.md b/path/to/file.md
--- a/path/to/file.md
+++ b/path/to/file.md
@@ -1,3 +1,3 @@
-old line
+new line
\`\`\`

---
```

## Use Cases

- **Pre-commit review**: Capture state before committing documentation changes
- **Change tracking**: Document what changed for a specific feature
- **Rollback reference**: Keep a record of previous content and diffs

---

Rendered by CodeBook [`549dabd`](codebook:codebook.version)
```

### Diff

```diff
diff --git a/.codebook/TASKS.md b/.codebook/TASKS.md
index b6cd961..cff79d0 100644
--- a/.codebook/TASKS.md
+++ b/.codebook/TASKS.md
@@ -14,17 +14,14 @@ This creates `.codebook/tasks/YYYYMMDD-TITLE_OF_THE_TASK.md` containing:
 
 Users can delete the tasks by running `codebook task delete` with the "Title of the task" or without it the pick tool will be used to select the task to delete from the list of tasks.
 
-## Options
-
-| Option | Description |
-|--------|-------------|
-| `--all` | Include all files, not just modified ones |
 
 ## Behavior
 
 By default, `task new` only includes files that have uncommitted changes (staged or unstaged). Use `--all` to capture all files regardless of git status.
 
 The title is converted to `UPPER_SNAKE_CASE` for the filename.
+And the task is prepended with a generic wrapper describing what to be changed.
+This wrapper can be customized by the user by adding -prefix and -suffix to `codebook.yml`
 
 ## Examples
 
@@ -83,4 +80,4 @@ diff --git a/path/to/file.md b/path/to/file.md
 
 ---
 
-Rendered by CodeBook [`549dabd`](codebook:codebook.version)
+Rendered by CodeBook [`549dabd`](codebook:codebook.version)
```

---

