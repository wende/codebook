# Cicada Integration

CodeBook integrates with [Cicada](https://github.com/cicada-lang/cicada) for live code exploration queries.

## Syntax

```html
<cicada endpoint="ENDPOINT" param1="value1" param2="value2">
RESULT
</cicada>
```

## Available Endpoints

### search-function

Search for functions by name:

<cicada endpoint="search-function" function_name="render" format="json" jq=".results[0].module" render="code[json]">

```json
_file_src.codebook.cli
```
</cicada>

**Parameters:**
- `function_name` (required) - Function name to search
- `module_name` (optional) - Limit to specific module

### search-module

Search for modules:

```html
<cicada endpoint="search-module" module_name="CodeBookParser" jq=".module,.location">
CodeBookParser  
src/codebook/parser.py:130
</cicada>
```

**Parameters:**
- `module_name` - Module name to find
- `file_path` - File path to search in

### query

Semantic code search:

```html
<cicada endpoint="query" keywords="authentication,login" scope="public">
Error: 422 Client Error: Unprocessable Content for url: http://localhost:9999/api/query
</cicada>
```

**Parameters:**
- `keywords` - Comma-separated search terms
- `pattern` - Module pattern (e.g., "MyApp.User.*")
- `scope` - `all` | `public` | `private`
- `filter_type` - `all` | `modules` | `functions`
- `show_snippets` - `true` | `false`

### git-history

Get git history for a file or module:

```html
<cicada endpoint="git-history" file_path="src/codebook/parser.py" limit="5">
## History for src/codebook/parser.py

- d3745315 (2025-12-28) @Krzysztof Wende: Format code with black
- 6c18359e (2025-12-28) @Krzysztof Wende: Update README and CLAUDE.md with Spec Driven Development focus
- 549dabdd (2025-12-28) @Krzysztof Wende: Add frontmatter parsing and configuration improvements
- 6a297a18 (2025-12-28) @Krzysztof Wende: A lot
- 3f2e42cb (2025-12-27) @Krzysztof Wende: Test commit
- 4f4a722c (2025-12-27) @Krzysztof Wende: INIT
</cicada>
```

**Parameters:**
- `file_path` - File path
- `module_name` - Module name
- `limit` - Max commits (default: 10)

## Response Formats

### JSON (default)

Returns structured JSON data:

<cicada endpoint="search-function" function_name="get_codebook_version" render="code[json]">

```json
{
  "query": "get_codebook_version",
  "total_matches": 1,
  "results": [
    {
      "module": "_file_src.codebook.renderer",
      "moduledoc": null,
      "function": "get_codebook_version",
      "arity": 0,
      "full_name": "_file_src.codebook.renderer.get_codebook_version/0",
      "signature": "def get_codebook_version() -> str:",
      "location": "src/codebook/renderer.py:23",
      "type": "public",
      "doc": "Get the current codebook version from git.\n\n    Returns:\n        Version string in format 'tag (short_sha)' or just 'sha' if no tag.",
      "call_sites": []
    }
  ]
}
```
</cicada>

### Markdown

Returns formatted markdown:

<cicada endpoint="search-function" function_name="get_codebook_version" format="markdown">
---
src/codebook/renderer.py:23
_file_src.codebook.renderer.get_codebook_version()
*No call sites found*

---
</cicada>

## JSON Path Extraction

Use the `jq` attribute to extract specific values from JSON responses:

### Extract a single field

```html
<cicada endpoint="search-function" function_name="render" jq=".total_matches">
2
</cicada>
```

### Extract nested value

```html
<cicada endpoint="search-function" function_name="render" jq=".results[0].module">
_file_src.codebook.cli
</cicada>
```

### Extract array of values

```html
<cicada endpoint="search-function" function_name="render" jq=".results[].location">
src/codebook/cli.py:132  
src/codebook/parser.py:94
</cicada>
```

## JQ Path Syntax

Supported expressions:
- `.key` - Access object key
- `[0]` - Access array index
- `[]` - Get all array elements
- `.key1.key2[0].key3` - Chained access

## Enabling Cicada

### Via CLI
```bash
codebook render docs/ --cicada --cicada-url http://localhost:9999
codebook watch docs/ --cicada
```

### Via codebook.yml
```yaml
cicada:
  enabled: true
  url: http://localhost:9999
  port: 9999
  start: true  # Auto-start cicada server
```

## Starting Cicada Server

```bash
# Manually
cicada serve --port 9999

# Or let codebook.yml handle it
codebook run  # Starts cicada if start: true
```

## Live Example

Functions in the renderer module:

<cicada endpoint="search-function" function_name="render_file" jq=".results[0].signature">
def render_file(
  self,
  path: Path,
  dry_run: bool = False
) -> RenderResult:
</cicada>

## Code
<cicada endpoint="search-module" file_path="cicada.py" format="json" jq=".location" render="code[python]">

```python
src/codebook/cicada.py:86
```
</cicada>

# Tests 
<cicada endpoint="search-module" file_path="tests/test_cicada.py" format="json" jq=".location" render="code[python]" what_calls_it="true" usage_type="tests">

```python
tests/test_cicada.py:8
```
</cicada>

--- BACKLINKS ---
[Cicada Integration](README.md "codebook:backlink")
