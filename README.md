# CodeBook: Dynamic Markdown Documentation with Live Code References

CodeBook is a markdown documentation system that embeds live code references using standard markdown link syntax. It maintains a single source of truth by storing templates in link URLs and dynamically rendering values inline.

## Features

- **Live Updates**: Automatically resolve code references from your backend service
- **Standard Markdown**: Uses existing markdown link syntax, works in any viewer
- **Single File**: No separate template/output files - everything in one markdown file
- **File Watching**: Auto-regenerate documents when files change with thread-safe debouncing
- **Git Integration**: Generate diffs with resolved values instead of templates
- **Fast**: Built-in TTL caching and efficient batch resolution
- **Extensible**: Easy to integrate with existing code intelligence backends
- **Code Execution**: Run Python code blocks via Jupyter kernels with output capture
- **Code Exploration**: Integrate with [Cicada](https://github.com/cicada-lang/cicada) for live code queries
- **Bidirectional Links**: Automatic backlink generation between markdown files
- **Task Management**: Capture documentation changes as actionable task files
- **Configuration File**: YAML-based config for zero-config startup with `codebook run`

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd codebook

# Install the package
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"
```

### Basic Usage

1. **Create a markdown file** with codebook links:
```markdown
# My Project
This project has [`42`](codebook:project.file_count) files.
The main language is [`Python`](codebook:project.primary_language).
```

2. **Initialize configuration**:
```bash
codebook init
```

3. **Run with auto-reload**:
```bash
codebook run
```

Or use explicit commands:
```bash
# One-time render
codebook render examples/ --base-url http://localhost:3000

# Watch for changes
codebook watch examples/ --base-url http://localhost:3000
```

## How It Works

CodeBook uses a special link format to embed dynamic values:

```markdown
CICADA supports [`13`](codebook:SCIP.language_count) languages.
```

- **Template**: `SCIP.language_count` (stored in the URL)
- **Value**: `13` (displayed in the link text)
- **Backticks**: Required for clean rendering in most viewers

When CodeBook processes the file:
1. Finds all `codebook:` links using regex pattern matching
2. Extracts template expressions from URLs
3. Resolves templates via HTTP calls to your backend service (with batch support)
4. Updates link text with resolved values
5. Preserves the original template in the URL

## Architecture

### Components

- **Link Parser** (`parser.py`): Finds and extracts codebook links from markdown (8 link types)
- **HTTP Client** (`client.py`): Resolves templates via backend service with TTL caching and batch support
- **File Renderer** (`renderer.py`): Updates markdown files with resolved values and manages backlinks
- **File Watcher** (`watcher.py`): Monitors files for changes with thread-safe debouncing
- **Git Diff Generator** (`differ.py`): Creates diffs with resolved values
- **Jupyter Kernel** (`kernel.py`): Executes Python code blocks with output capture
- **Cicada Client** (`cicada.py`): Code exploration queries with jq extraction
- **Configuration** (`config.py`): YAML-based configuration management
- **CLI Interface** (`cli.py`): User-friendly command-line interface

### Backend Integration

CodeBook expects your backend to expose endpoints:

**Single Resolution:**
```
GET /resolve/{template_expression}
Response: {"value": "resolved_value"}
```

**Batch Resolution (optional but recommended):**
```
POST /resolve/batch
Body: {"templates": ["template1", "template2"]}
Response: {"values": {"template1": "value1", "template2": "value2"}}
```

**Health Check:**
```
GET /health
Response: 200 OK
```

Example:
```bash
curl http://localhost:3000/resolve/SCIP.language_count
# Returns: {"value": 13}
```

## CLI Commands

### Global Options

These options apply to all commands:
```bash
codebook [global-options] <command> [options]

Global Options:
  -b, --base-url    Backend service URL (env: CODEBOOK_BASE_URL)
  -t, --timeout     HTTP request timeout in seconds (default: 10)
  -c, --cache-ttl   Cache time-to-live in seconds (default: 60)
  --cicada-url      Cicada server URL (env: CICADA_URL)
  -v, --verbose     Enable verbose logging output
  --version         Show version
```

### Run (Recommended)
```bash
codebook run [options]

Options:
  -c, --config    Path to config file (searches for codebook.yml if not provided)
```

Runs CodeBook using `codebook.yml` configuration. Auto-starts backend and Cicada services if configured, performs initial render, and watches for changes.

### Initialize Config
```bash
codebook init [options]

Options:
  -o, --output    Output file path (default: codebook.yml)
```

Creates a default `codebook.yml` configuration file.

### Render Directory
```bash
codebook render <directory> [options]

Options:
  --recursive/--no-recursive    Process subdirectories (default: true)
  --dry-run                     Show changes without modifying files
  --exec/--no-exec              Execute Python code blocks via Jupyter
  --cicada/--no-cicada          Execute Cicada code exploration queries
```

### Watch Directory
```bash
codebook watch <directory> [options]

Options:
  -d, --debounce                Debounce time in seconds (default: 0.5)
  --initial-render/--no-initial-render  Render before watching (default: true)
  --recursive/--no-recursive    Watch subdirectories (default: true)
  --exec/--no-exec              Enable code execution via Jupyter
  --cicada/--no-cicada          Enable Cicada queries
```

### Generate Diff
```bash
codebook diff <path> [options]

Options:
  -r, --ref         Git ref to compare against (default: HEAD)
  -o, --output      Output file for diff (default: stdout)
  --recursive       Process subdirectories (for directories)
```

### Show Rendered Content
```bash
codebook show <file>
```

### Task Management
```bash
# Create a task from modified files
codebook task new <title> <scope> [options]

Options:
  --all    Include all files, not just modified ones

# List all tasks
codebook task list

# Delete a task
codebook task delete [title] [options]

Options:
  -f, --force    Delete without confirmation
```

Tasks capture git diffs of modified files in `.codebook/tasks/YYYYMMDDHHMM-TITLE.md`.

### Health Check
```bash
codebook health
```

### Clear Cache
```bash
codebook clear-cache
```

## Examples

The `examples/` directory contains sample markdown files and a mock backend server.

To test with the examples:
```bash
# Terminal 1: Start mock backend
python examples/mock_server.py

# Terminal 2: Render all examples
codebook render examples/ --base-url http://localhost:3000

# Or watch for changes
codebook watch examples/ --base-url http://localhost:3000
```

## Link Syntax

CodeBook supports multiple link formats:

### Inline Links (Primary)
```markdown
[`VALUE`](codebook:TEMPLATE)
```
Example: `[`13`](codebook:SCIP.language_count)` displays "13"

### URL Links
```markdown
[Link Text](URL "codebook:TEMPLATE")
```
The URL updates on resolution while link text stays the same.

### HTML Elements
```html
<span data-codebook="TEMPLATE">VALUE</span>
<div data-codebook="TEMPLATE">MULTILINE CONTENT</div>
```

### Code Execution Blocks
```html
<exec lang="python">
print("Hello, World!")
</exec>
<output>
Hello, World!
</output>
```
Requires `--exec` flag or `exec: true` in config.

### Cicada Query Blocks
```html
<cicada endpoint="search-function" function_name="render" format="markdown">
Results appear here
</cicada>
```
Requires `--cicada` flag or `cicada.enabled: true` in config.

### Special Templates

- `codebook.version` - Returns git commit SHA or tag

## Template Patterns

Template expressions are resolved via HTTP:

```markdown
# Simple properties
[`13`](codebook:SCIP.language_count)

# Nested properties
[`1247`](codebook:project.metrics.total_files)

# API metrics
[`127`](codebook:API.endpoint_count)

# Status values
[`Passing`](codebook:CI.build_status)

# Performance metrics
[`145ms`](codebook:API.get_response_time)
```

## Backend Integration

### Implementing a Backend Service

Your backend service needs to resolve template expressions and return values. Here's a Python example using Flask:

```python
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/resolve/<path:template>')
def resolve_template(template):
    # Your logic to resolve the template
    value = resolve_your_template(template)
    return jsonify({"value": str(value)})

@app.route('/resolve/batch', methods=['POST'])
def resolve_batch():
    templates = request.json.get("templates", [])
    values = {t: resolve_your_template(t) for t in templates}
    return jsonify({"values": values})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})
```

### Template Validation

Templates should follow these guidelines:
- Use dot notation for nested properties (e.g., `project.metrics.files`)
- Avoid special characters that might break URLs
- Keep templates descriptive and readable
- Use consistent naming conventions

## Bidirectional Links

CodeBook automatically generates backlinks when you link to other markdown files:

```markdown
See the [API Documentation](api.md) for details.
```

When rendered, `api.md` will have a backlinks section added:

```markdown
--- BACKLINKS ---
[API Documentation](source.md "codebook:backlink")
```

Features:
- Automatic deduplication
- Relative path calculation
- Creates BACKLINKS section if needed

## Configuration File

Create `codebook.yml` for zero-config startup:

```yaml
watch_dir: .codebook
tasks_dir: .codebook/tasks
exec: true
recursive: true
timeout: 10.0
cache_ttl: 60.0

backend:
  url: http://localhost:3000
  port: 3000
  start: true

cicada:
  enabled: true
  url: http://localhost:9999
  port: 9999
  start: true

# Optional task customization
task_prefix: |
  # Instructions for AI
  ...
task_suffix: ""
```

Then simply run:
```bash
codebook run
```

## Code Execution

Execute Python code blocks with Jupyter kernel integration:

```html
<exec lang="python">
import math
print(f"Pi = {math.pi:.4f}")
</exec>
<output>
Pi = 3.1416
</output>
```

Features:
- State persists between blocks
- Project modules available via `sys.path`
- Errors captured with stripped ANSI codes

Enable via `--exec` flag or `exec: true` in config.

## Cicada Integration

Query your codebase with live code exploration:

```html
<cicada endpoint="search-function" function_name="render" format="markdown">
Function results...
</cicada>
```

Available endpoints:
- `query` - Semantic code search
- `search-function` - Find function definitions
- `search-module` - Find module information
- `git-history` - Get git history

Supports jq extraction:
```html
<cicada endpoint="search-function" function_name="render" jq=".total_matches">
42
</cicada>
```

Enable via `--cicada` flag or `cicada.enabled: true` in config.

## Detailed Documentation

For comprehensive documentation, see the `.codebook/` directory:

- **[Link Syntax](.codebook/LINK_SYNTAX.md)** - All 8 link type formats
- **[Code Execution](.codebook/CODE_EXECUTION.md)** - Jupyter kernel details
- **[Cicada Integration](.codebook/CICADA_INTEGRATION.md)** - All endpoints and jq queries
- **[Configuration](.codebook/CONFIGURATION.md)** - Full YAML reference
- **[Tasks](.codebook/TASKS.md)** - Task management details
- **[Edge Cases](.codebook/edge-cases/)** - Implementation behavior details

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=codebook --cov-report=html

# Run specific test file
pytest tests/test_client.py -v

# Run with verbose output
pytest -v
```

## Development

### Project Structure
```
codebook/
├── src/codebook/       # Main package (src layout)
│   ├── __init__.py
│   ├── parser.py       # Link parsing (8 types)
│   ├── client.py       # HTTP client with caching
│   ├── renderer.py     # File rendering + backlinks
│   ├── watcher.py      # File watching with debouncing
│   ├── differ.py       # Git diff generation
│   ├── kernel.py       # Jupyter code execution
│   ├── cicada.py       # Code exploration client
│   ├── config.py       # YAML configuration
│   └── cli.py          # Command-line interface
├── tests/              # Comprehensive test suite
├── examples/           # Example markdown files
│   └── mock_server.py  # Mock backend for testing
├── .codebook/          # Detailed documentation
│   ├── LINK_SYNTAX.md
│   ├── CODE_EXECUTION.md
│   ├── CICADA_INTEGRATION.md
│   ├── CONFIGURATION.md
│   ├── TASKS.md
│   └── edge-cases/     # Implementation details
├── pyproject.toml      # Project configuration
└── README.md           # This file
```

### Code Quality

The project uses modern Python tooling:
- **Black** for code formatting
- **Ruff** for linting
- **pytest** for testing

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Run tests
pytest
```

### Key Design Decisions

1. **Single-file approach**: No separate template/output files - everything in one markdown file
2. **Standard markdown**: Uses existing link syntax, works in any markdown viewer
3. **Template preservation**: Template always stored in URL, survives regeneration
4. **HTTP backend**: Decoupled from code intelligence logic, just calls existing service
5. **Backticks for clean rendering**: Suppresses link styling in most viewers
6. **Thread-safe debouncing**: Prevents excessive re-renders during rapid edits
7. **Batch resolution with fallback**: Uses batch endpoint when available, falls back to individual requests

## Integration Examples

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Update Documentation
  run: |
    pip install -e .
    codebook render docs/ --base-url ${{ secrets.BACKEND_URL }}
    git config user.name "GitHub Actions"
    git config user.email "actions@github.com"
    git add docs/
    git diff --staged --quiet || git commit -m "Update documentation"
    git push
```

### Pre-commit Hook
```bash
#!/bin/sh
# .git/hooks/pre-commit
codebook render docs/ --base-url http://localhost:3000
git add docs/
```

## Performance

- **TTL Caching**: HTTP responses cached with configurable time-to-live
- **Batch Resolution**: Resolve multiple templates in a single HTTP request
- **Debouncing**: File changes debounced to avoid excessive processing
- **Selective Updates**: Only files with codebook links are processed
- **Efficient Parsing**: Regex-based link detection optimized for performance

## Troubleshooting

### Common Issues

1. **Backend connection failed**
   - Check backend URL and network connectivity
   - Verify backend service is running: `codebook health`
   - Check firewall settings

2. **Templates not resolving**
   - Verify template syntax matches backend expectations
   - Check backend logs for resolution errors
   - Clear cache and retry: `codebook clear-cache`

3. **Files not updating**
   - Check if files contain valid codebook links
   - Verify file permissions
   - Use `--dry-run` to see what would change

### Debug Mode
```bash
# Enable verbose output
codebook -v render docs/ --base-url http://localhost:3000
```

## What CodeBook Does NOT Do

- Does NOT parse/analyze code directly
- Does NOT implement code intelligence features
- Does NOT require custom markdown preview extensions
- Does NOT create duplicate files or sidecar indexes

The backend service handles all code analysis. CodeBook is purely a rendering layer that bridges markdown documentation with live code data.

## License

MIT License
