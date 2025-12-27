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

2. **Start the mock backend** (for testing):
```bash
python examples/mock_server.py
```

3. **Render the document**:
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

- **Link Parser** (`parser.py`): Finds and extracts codebook links from markdown
- **HTTP Client** (`client.py`): Resolves templates via backend service with TTL caching and batch support
- **File Renderer** (`renderer.py`): Updates markdown files with resolved values
- **File Watcher** (`watcher.py`): Monitors files for changes with thread-safe debouncing
- **Git Diff Generator** (`differ.py`): Creates diffs with resolved values
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

### Render Directory
```bash
codebook render <directory> [options]

Options:
  -b, --base-url    Backend service URL (default: http://localhost:3000)
  -t, --timeout     HTTP request timeout in seconds (default: 10)
  -c, --cache-ttl   Cache time-to-live in seconds (default: 60)
  --recursive       Process subdirectories recursively (default: true)
  --dry-run         Show what would be done without making changes
```

### Watch Directory
```bash
codebook watch <directory> [options]

Options:
  -b, --base-url         Backend service URL
  -d, --debounce         Debounce time in seconds (default: 0.5)
  --initial-render       Render files once before watching (default: true)
  --recursive            Watch subdirectories recursively (default: true)
```

### Generate Diff
```bash
codebook diff <path> [options]

Options:
  -b, --base-url    Backend service URL
  -r, --ref         Git ref to compare against (default: HEAD)
  -o, --output      Output file for diff (default: stdout)
  --recursive       Process subdirectories recursively (for directories)
```

### Show Rendered Content
```bash
codebook show <file> [options]

Options:
  -b, --base-url    Backend service URL
```

### Check Backend Health
```bash
codebook health [options]

Options:
  -b, --base-url    Backend service URL
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

## Template Patterns

CodeBook supports various template patterns:

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
│   ├── parser.py       # Link parsing logic
│   ├── client.py       # HTTP client with caching
│   ├── renderer.py     # File rendering logic
│   ├── watcher.py      # File watching with debouncing
│   ├── differ.py       # Git diff generation
│   └── cli.py          # Command-line interface
├── tests/              # Comprehensive test suite
├── examples/           # Example markdown files
│   └── mock_server.py  # Mock backend for testing
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
