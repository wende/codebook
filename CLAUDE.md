# CodeBook Project Guide

## Overview

CodeBook is a markdown documentation system that embeds live code references using standard markdown link syntax. It resolves template expressions via HTTP calls to a backend service and updates markdown files in-place.

**Link format:** `[`VALUE`](codebook:TEMPLATE)`

Example: `[`13`](codebook:SCIP.language_count)` displays "13" and resolves the template `SCIP.language_count` from the backend.

## Project Structure

```
codebook/
├── src/codebook/           # Main package (src layout)
│   ├── __init__.py         # Package exports
│   ├── parser.py           # Link parsing with regex
│   ├── client.py           # HTTP client with TTL caching
│   ├── renderer.py         # File rendering logic
│   ├── watcher.py          # File watching with debouncing
│   ├── differ.py           # Git diff generation
│   └── cli.py              # Click-based CLI
├── tests/                  # pytest test suite (112 tests)
│   ├── conftest.py         # Shared fixtures
│   ├── test_parser.py
│   ├── test_client.py
│   ├── test_renderer.py
│   ├── test_watcher.py
│   ├── test_differ.py
│   └── test_cli.py
├── examples/
│   ├── mock_server.py      # Flask mock backend for testing
│   └── example.md          # Sample markdown with codebook links
├── pyproject.toml          # Project config (Black, Ruff, pytest)
└── README.md               # User documentation
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

### CLI (`cli.py`)
- Built with Click
- Commands: `render`, `watch`, `diff`, `show`, `health`, `clear-cache`
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

1. **src/ layout**: Proper package isolation, prevents import confusion
2. **Dataclasses over dicts**: Type safety for results (`RenderResult`, `DiffResult`, `CacheEntry`)
3. **Batch with fallback**: Try efficient batch endpoint, fall back to individual requests
4. **Thread-safe debouncing**: Prevents race conditions in file watcher
5. **Click for CLI**: Declarative, well-tested, good help generation
6. **responses library for tests**: Clean HTTP mocking without server overhead

## Dependencies

**Runtime:**
- `click>=8.1.0` - CLI framework
- `watchdog>=3.0.0` - File system monitoring
- `requests>=2.31.0` - HTTP client

**Development:**
- `pytest>=7.4.0` - Testing
- `pytest-cov>=4.1.0` - Coverage
- `responses>=0.23.0` - HTTP mocking
- `flask>=2.0.0` - Mock server
- `black>=23.0.0` - Formatting
- `ruff>=0.1.0` - Linting

## Environment Variables

- `CODEBOOK_BASE_URL`: Default backend URL (fallback: `http://localhost:3000`)


<cicada>
  **PRIMARY: Always use `mcp__cicada__query` for understanding Elixir code.**

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
