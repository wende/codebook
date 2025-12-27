# Tasks with dates

## TODO

Implement the following changes to the task management feature:

### 1. Add date prefix to task filenames

**File:** `src/codebook/cli.py` (around line 643, `task_new` function)

**Current behavior:** Creates `.codebook/tasks/TITLE_OF_THE_TASK.md`

**Target behavior:** Creates `.codebook/tasks/YYYYMMDD-TITLE_OF_THE_TASK.md`

**Implementation:**
- Use `datetime.date.today().strftime("%Y%m%d")` to get the date prefix
- Prepend to the filename: `f"{date_prefix}-{title_snake}.md"`

### 2. Add `task delete` command

**File:** `src/codebook/cli.py`

**New command:** `codebook task delete [TITLE]`

**Behavior:**
- If `TITLE` provided: Delete the matching task file
- If no `TITLE`: Use an interactive picker (e.g., `pick` library or `click.Choice`) to select from existing tasks
- Should match tasks by title (ignoring the date prefix)

**Implementation:**
- Add new `@task.command("delete")` function
- List files in `.codebook/tasks/` directory
- Parse filenames to extract titles (strip date prefix and `.md` extension)
- If interactive: present choices using `click.prompt` with type `click.Choice`
- Delete selected file with confirmation

### 3. Update documentation

**File:** `.codebook/TASKS.md`

Update to reflect the new filename format and delete command.

---

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

## Options

| Option | Description |
|--------|-------------|
| `--all` | Include all files, not just modified ones |

## Behavior

By default, `task new` only includes files that have uncommitted changes (staged or unstaged). Use `--all` to capture all files regardless of git status.

The title is converted to `UPPER_SNAKE_CASE` for the filename.

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

Rendered by CodeBook [`6742eaf`](codebook:codebook.version)
```

### Diff

```diff
diff --git a/.codebook/TASKS.md b/.codebook/TASKS.md
index 4faa3e2..b6cd961 100644
--- a/.codebook/TASKS.md
+++ b/.codebook/TASKS.md
@@ -8,10 +8,12 @@ CodeBook includes a task management feature for capturing documentation changes.
 codebook task new "Title of the task" ./scope
 ```
 
-This creates `.codebook/tasks/TITLE_OF_THE_TASK.md` containing:
+This creates `.codebook/tasks/YYYYMMDD-TITLE_OF_THE_TASK.md` containing:
 - Current content of each modified file
 - Git diff showing changes from HEAD
 
+Users can delete the tasks by running `codebook task delete` with the "Title of the task" or without it the pick tool will be used to select the task to delete from the list of tasks.
+
 ## Options
 
 | Option | Description |
@@ -81,4 +83,4 @@ diff --git a/path/to/file.md b/path/to/file.md
 
 ---
 
-Rendered by CodeBook [`6742eaf`](codebook:codebook.version)
+Rendered by CodeBook [`6742eaf`](codebook:codebook.version)
```

---

