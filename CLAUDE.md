# CodeBook Project Guide

## Overview

CodeBook is a **Doc Driven Development** framework for AI agents.

**Workflow:**
1. Write feature docs in markdown (`.codebook/` directory)
2. CodeBook renders live values, executes code, and queries your codebase
3. Turn doc changes into tasks via `codebook task new "Title" ./scope`
4. Feed tasks to AI agents for implementation

**Key capabilities:**
- `[`value`](codebook:server.template)` — Dynamic values from backend
- `<exec lang="python">` — Execute Python via Jupyter
- `<cicada endpoint="...">` — Live code exploration queries
- `[text](file.md)` — Bidirectional links with auto-backlinks
- Task generation from git diffs of doc changes

## Project Structure

```
codebook/
├── src/codebook/           # Main package
│   ├── cli.py              # Click CLI (run, init, render, watch, task, diff, etc.)
│   ├── config.py           # YAML configuration (codebook.yml)
│   ├── parser.py           # Link parsing (8 types: inline, url, span, div, exec, cicada, etc.)
│   ├── renderer.py         # File rendering + backlink generation
│   ├── client.py           # HTTP client with TTL caching
│   ├── kernel.py           # Jupyter kernel for code execution
│   ├── cicada.py           # Cicada API client for code exploration
│   ├── watcher.py          # File watching with debouncing
│   └── differ.py           # Git diff generation
├── tests/                  # pytest test suite
├── codebook/               # Documentation (uses CodeBook itself)
└── pyproject.toml          # Project config
```

## Key Components

### Parser (`parser.py`)
- `CodeBookParser`: Extracts codebook links from markdown using regex
- `CodeBookLink`: Dataclass representing a found link (value, template, position)
- Pattern: `\[`([^`]*)`\]\(codebook:([^)]+)\)`

### Client (`client.py`)
- `CodeBookClient`: HTTP client for template resolution
- TTL-based caching with `CacheEntry` dataclass
- Batch resolution via POST `/resolve/batch` with fallback to individual GET requests
- Health check endpoint support

### Renderer (`renderer.py`)
- `CodeBookRenderer`: Orchestrates parsing and HTTP resolution
- `RenderResult`: Dataclass with render statistics (templates_found, templates_resolved, changed)
- Supports dry-run mode and directory recursion

### Watcher (`watcher.py`)
- `CodeBookWatcher`: File system watcher using watchdog
- `DebouncedHandler`: Thread-safe debouncing to prevent rapid re-renders
- Supports async start for background watching

### Differ (`differ.py`)
- `CodeBookDiffer`: Generates git diffs with resolved values
- `DiffResult`: Dataclass with diff output and error handling
- Uses `git show` and `difflib` for comparison

### Kernel (`kernel.py`)
- `CodeBookKernel`: Jupyter kernel wrapper for Python execution
- Executes `<exec lang="python">` blocks
- State persists between blocks in same session

### Cicada (`cicada.py`)
- `CicadaClient`: HTTP client for Cicada code exploration
- Endpoints: `query`, `search-function`, `search-module`, `git-history`
- `jq_query()`: Extract values from JSON responses

### Config (`config.py`)
- `CodeBookConfig`: YAML configuration dataclass
- Loads from `codebook.yml` or searches parent directories
- Configures main_dir, tasks_dir (relative to main_dir), backend, cicada settings

### CLI (`cli.py`)
- Built with Click
- **Core:** `run` (main entry), `init`, `render`, `watch`
- **Tasks:** `task new`, `task list`, `task delete`
- **Utils:** `diff`, `show`, `health`, `clear-cache`
- Global options: `--base-url`, `--timeout`, `--cache-ttl`, `--verbose`

## Backend API Contract

The backend must implement:

```
GET /resolve/{template}
Response: {"value": "resolved_value"}

POST /resolve/batch (optional, improves performance)
Body: {"templates": ["t1", "t2"]}
Response: {"values": {"t1": "v1", "t2": "v2"}}

GET /health
Response: 200 OK
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=codebook --cov-report=html

# Run specific test file
pytest tests/test_client.py -v
```

## Common Tasks

### Adding a new CLI command
1. Add function in `cli.py` with `@main.command()` decorator
2. Use `@click.pass_context` to access the shared client
3. Add tests in `tests/test_cli.py`

### Modifying the link pattern
1. Update `LINK_PATTERN` regex in `parser.py`
2. Update `CodeBookLink.render()` method
3. Update tests in `tests/test_parser.py`

### Adding new HTTP endpoints
1. Add method to `CodeBookClient` in `client.py`
2. Add mock responses in tests using `@responses.activate`

## Code Style

- **Formatter:** Black (line-length: 100)
- **Linter:** Ruff (E, F, W, I, N, UP, B, C4)
- **Type hints:** Python 3.10+ style (`str | None`, `list[str]`)
- **Docstrings:** Google style

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/
```

## Design Decisions

1. **Doc Driven Development**: Docs are the source of truth; code implements them
2. **Standard markdown**: All syntax renders normally in any viewer (GitHub, VSCode, etc.)
3. **Template preservation**: Template stays in URL, value updates in-place — re-render anytime
4. **Dataclasses over dicts**: Type safety for results (`RenderResult`, `DiffResult`, `CacheEntry`)
5. **Batch with fallback**: Try efficient batch endpoint, fall back to individual requests
6. **Thread-safe debouncing**: Prevents race conditions in file watcher

## Dependencies

**Runtime:**
- `click` - CLI framework
- `requests` - HTTP client
- `watchdog` - File system monitoring
- `pyyaml` - Configuration parsing
- `jupyter-client` - Code execution

**Development:**
- `pytest`, `pytest-cov` - Testing
- `responses` - HTTP mocking
- `black`, `ruff` - Formatting/linting

## Environment Variables

- `CODEBOOK_BASE_URL`: Default backend URL (fallback: `http://localhost:3000`)


<cicada>
  **PRIMARY: Always use `mcp__cicada__query` for ALL code exploration and discovery.**

  Cicada beats builtin tools for code exploration:
  - **vs Grep**: Semantic search by purpose, not literal text. Finds "authentication logic" without knowing exact function names. Understands code relationships and string literals semantically.
  - **vs Glob**: Discovers modules by functionality, not file names. Finds "rate limiting" without knowing it's in `lib/my_app/plugs/rate_limiter.ex`.
  - **vs Read**: Tells you WHICH files to read and WHY they're relevant. Shows connections between modules so you read the right files in the right order.

  ## Usage
  Query by keywords `['authentication', 'login']` or patterns `'MyApp.User.*'` or both.
  Follow returned suggestions - they tell you which specialized tool to use next.

  ## Parameters
  - `scope`: 'all' | 'public' | 'private'
  - `filter_type`: 'all' | 'modules' | 'functions'
  - `match_source`: 'all' | 'docs' | 'strings' (semantic search in code strings)
  - `recent`: true (14 days) | false (all time, default)
  - `path_pattern`: 'lib/auth/**' or '!**/test/**' (! negates)
  - `show_snippets`: true | false (default)

  ## Workflow
  1. `query(['jwt'])` → semantic matches + relationships + suggestions
  2. Follow suggestion → explore connections/usage
  3. Repeat → understand functionality

  Use Grep/Glob/Read only for non-Elixir files or when you already have exact paths/strings.
</cicada>
- When addressing comments using make pr-comments remember to add the word 'addressed' in the commit message