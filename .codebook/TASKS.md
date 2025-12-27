# Task Management

CodeBook includes a task management feature for capturing documentation changes.

## Creating a Task

```bash
codebook task new "Title of the task" ./scope
```

This creates `.codebook/tasks/YYYYMMDDHHMM-TITLE_OF_THE_TASK.md` containing git diffs for each modified file.

Users can delete the tasks by running `codebook task delete` with the "Title of the task" or without it the pick tool will be used to select the task to delete from the list of tasks.


## Behavior

By default, `task new` only includes files that have uncommitted changes (staged or unstaged).

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

\`\`\`diff
diff --git a/path/to/file.md b/path/to/file.md
--- a/path/to/file.md
+++ b/path/to/file.md
@@ -1,3 +1,3 @@
-old line
+new line
\`\`\`
```

## Use Cases

- **Pre-commit review**: Capture state before committing documentation changes
- **Change tracking**: Document what changed for a specific feature
- **Rollback reference**: Keep a record of previous content and diffs

---

Rendered by CodeBook [`ee158b4`](codebook:codebook.version)
