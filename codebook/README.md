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

# Run with documentation hot-reloading
codebook run
```

## Features

- **[Syntax](SYNTAX.md)** - Embed dynamic values in markdown
- **[Templates](TEMPLATES.md)** - Available templates and resolution
- **[Client/Server](CLIENT_SERVER.md)** - Architecture and API contract
- **[Code Execution](CODE_EXECUTION.md)** - Run Python code blocks
- **[Cicada Integration](CICADA_INTEGRATION.md)** - Live code exploration
- **[Configuration](CONFIGURATION.md)** - YAML config reference
- **[Frontmatter](FRONTMATTER.md)** - YAML frontmatter support
- **[Tasks](TASKS.md)** - Task management
- **[AI Helpers](AI_HELPERS.md)** - AI helpers for task review
- **[Edge Cases](edge-cases/README.md)** - Implementation details and behaviors
- **[Utils](UTILS.md)** - Utility functions and helpers

## CLI Commands

### Core Commands
- `codebook run` - Run with codebook.yml config (auto-starts services, watches for changes)
- `codebook init` - Create default codebook.yml configuration
- `codebook render <dir>` - One-time render of markdown files
- `codebook watch <dir>` - Watch directory and auto-render on changes

### Utility Commands
- `codebook diff <path>` - Generate git diff with resolved values
- `codebook show <file>` - Display rendered content of a file
- `codebook health` - Check backend service health
- `codebook clear-cache` - Clear template resolution cache

### Task Management
- `codebook task new <title> <scope>` - Create task from modified files
- `codebook task list` - List all existing tasks
- `codebook task delete [title]` - Delete a task (interactive if no title)

## Project Stats

| Metric    | Value                               |
| --------- | ----------------------------------- |
| Version   | [`v0.1.1-5-g8afa31a`](codebook:codebook.version)  |

## Documentation Files

[Docs](./codebook)

---
 
