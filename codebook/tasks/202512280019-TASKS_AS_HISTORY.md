This file is a diff of a feature specification. I want you to change the code to match the new spec.

# Tasks as history

--- FEATURE TASK ---
Add default task suffix to task creation. When creating a new task via `codebook task new`, the task file should include a default suffix with instructions for documenting the completed work, containing sections for FEATURE TASK, NOTES, and SOLUTION.

--- NOTES ---
The task-prefix was already implemented and using the correct default value. Only the task-suffix needed to be added with a proper default.

--- SOLUTION ---
Added `DEFAULT_TASK_SUFFIX` constant in `config.py` with the specified format. Updated the `CodeBookConfig` dataclass to use this constant as the default for `task_suffix`. Updated `_from_dict` and `to_dict` methods to handle the new default correctly. All 200 tests pass.
