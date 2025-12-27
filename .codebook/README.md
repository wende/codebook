# CodeBook Documentation

Spec Driven Development framework.
Document features in markdown in you `.codebook` directory.
Each change can be turned into a task by running `codebook task new "Title of the task" ./scope` [Tasks](TASKS.md)
These tasks are actionable pieces of work that can be fed to an AI agent to implement.

## Overview

CodeBook transforms static markdown into living documentation by embedding dynamic values, executable code, and live code exploration queries.

## Quick Start

```bash
# Initialize a config file
codebook init

# Run with auto-reload
codebook run
```

## Features

- **[Link Syntax](LINK_SYNTAX.md)** - Embed dynamic values in markdown
- **[Code Execution](CODE_EXECUTION.md)** - Run Python code blocks
- **[Cicada Integration](CICADA_INTEGRATION.md)** - Live code exploration
- **[Configuration](CONFIGURATION.md)** - YAML config reference

## Project Stats

| Metric    | Value                               |
| --------- | ----------------------------------- |
| Templates | [`42`](codebook:project.file_count) |
| Version   | [`ee158b4`](codebook:codebook.version)  |

## Documentation Files

[Docs](./codebook)

---

Rendered by CodeBook [`ee158b4`](codebook:codebook.version)
