# Task Management

CodeBook includes a task management feature for capturing documentation changes.

## Creating a Task

```bash
codebook task new "Title of the task" ./scope
```

This creates `.codebook/tasks/TITLE_OF_THE_TASK.md` containing:
- Current content of each modified file
- Git diff showing changes from HEAD

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

Rendered by CodeBook [`4f4a722`](codebook:codebook.version)
