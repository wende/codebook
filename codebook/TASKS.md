# Task Management

CodeBook includes a task management feature for capturing documentation changes.

## Creating a Task

```bash
codebook task new "Title of the task" ./scope
```

This creates `.codebook/tasks/YYYYMMDDHHMM-TITLE_OF_THE_TASK.md` containing git diffs for each modified file.

In case documentation files were modified during the task execution you can run
```bash
codebook task update ./PATH_TO_THE_TASK_FILE ./scope

```
This will update the task file with the new diffs to the documentation files in the scope.

## Listing Tasks

View all existing tasks:

```bash
codebook task list
```

Shows all task files with formatted dates:
```
Tasks:
  [2025-12-28 00:19] TASKS_AS_HISTORY
  [2025-12-27 23:30] BIDIRECTIONAL_LINKS
  [2025-12-27] CODEBOOK_TAGS
```

## Deleting Tasks

Delete a task by title:

```bash
codebook task delete "Title of the task"
```

Or run without a title for an interactive picker:

```bash
codebook task delete
```

Options:
- `--force` or `-f`: Delete without confirmation


## Prefix and Suffix

The task is prepended with a generic wrapper describing what to be changed.
This wrapper can be customized by the user by adding -prefix and -suffix to `codebook.yml`

```yaml
task-prefix: "## TODO: "
task-suffix: "
```

By default the prefix is: 
```markdown
This file is a diff of a feature specification. I want you to change the code to match the new spec.
```
And the suffix is:
```markdown
---
After completing the task, please update the task file with:
- Description of the feature task that was requested
- Short description of the changes that were made and why
Do not include code snippets. Only describe the functional changes that were made.
Do not remove diff lines from the task file.
--- FEATURE TASK ---
...
--- NOTES ---
...
--- SOLUTION ---
```

## Behavior

By default, `task new` only includes files that have uncommitted changes (staged or unstaged).


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

\`\`\`diff
diff --git a/path/to/file.md b/path/to/file.md
--- a/path/to/file.md
+++ b/path/to/file.md
@@ -1,3 +1,3 @@
-old line
+new line
\`\`\`
```

## Worktrees
```bash
codebook task new "Theme Support" ./docs --worktree
```

Creates new worktree for task
Copies uncommitted doc changes to worktree
Reverts scoped doc changes on the source branch 
The task is created in the worktree instead of the source branch.
This prepares a new isolated environment to work in without affecting the source branch.
The worktree is created in the `../{rootdir}-{task-title}` directory on a `task-{task-title}` branch 

## Use Cases

- **Pre-commit review**: Capture state before committing documentation changes
- **Change tracking**: Document what changed for a specific feature
- **Rollback reference**: Keep a record of previous content and diffs


## Coverage

To get the coverage of the tasks, run:
```bash
codebook task coverage [scope]
```
This will get all of the commits that have been made with the tasks by using git blame,
and intersect them with the git blame of the project.
You will get a percentage of coverage for each file in the project.
If you provide a path glob, it will only show the coverage for the specific scope.

```bash
codebook task coverage --detailed
```
This will show a detailed report of the coverage for each file line, 
showing the last task that covered the line or if the line is not covered.

```bash
codebook task coverage --short
```
This will show the score of the coverage for the project.
The score is calculated by the percentage of covered lines divided by the total number of lines in the project. You can use it in the CI/CD to track the code documentation coverage of the project.

E.g `95.4% (9847/10327 lines)`

## Stats

---
To get the stats of the tasks, run:
```bash
codebook task stats
```
This will show the stats of the tasks sorted by the data from the most recent
The stats are calculated for each task by 
 - the number of commits, 
 - the number of lines covered by the task.
 - features modified by the task 

Rendered by CodeBook [`dev`](codebook:codebook.version)

--- BACKLINKS ---
[Tasks](README.md "codebook:backlink")
