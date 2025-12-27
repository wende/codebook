
 User can run
 ```bash
 codebook task new "Title of the task" ./folder_for_git_diff_scope
 ```

Which will create a 
  .codebook/tasks/TITLE_OF_THE_TASK.md
  
  With contents:
  ---
  1. path/ChangedFile.md
  ```
  Original rendered content
  ```
  Diff:
  - Removed rendered line
  + Added rendered line
---

## For example

```
codebook task new "Task creation" ./TASKS.md
```

### ./tasks/TASK_CREATION.md
---
1. ./TASKS.md
   
   [BEFORE]
   [DIFF]
   