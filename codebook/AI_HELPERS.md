# AI Helpers

CodeBook provides a set of AI helpers to help you with your work.

## AI Helper Commands

### `codebook ai help`

Shows the help for the AI helpers.

### `codebook ai review [agent] [path] -- [agent_args]`

Reviews the task with the given agent and path.

Supported agents:
- claude
- codex
- gemini
- opencode
- kimi

Agent arguments are passed to the agent as command line arguments.
Review starts an agent with a specific prompt, that can be customized in the [codebook.yml](./CONFIGURATION.md) config file.
Default prompt is:
```
You are a helpful assistant that reviews the task and provides feedback.
You are given a task file that contains a diff of the changes that were made to the codebase.
You need to read the original feature documents that were changed, as well as the diff, and provide feedback on the changes that were made to the codebase. Make sure the documentation describes accurately the changes' functionality.
Append your feedback to the task file starting with the --- REVIEW YYYYMMDDHHMM --- on top. Do not change any other parts of the task file.


This is the task file: [TASK_FILE]
```

#### Examples
```bash
codebook ai review claude ./codebook/tasks/YYYYMMDDHHMM-TITLE.md
```

--- BACKLINKS ---
[AI Helpers](README.md "codebook:backlink")
