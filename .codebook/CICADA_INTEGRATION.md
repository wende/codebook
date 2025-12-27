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

<cicada endpoint="search-function" function_name="render" format="markdown">
Functions matching render

Found 2 match(es):

---

_file_src.codebook.cli.render()
src/codebook/cli.py:108
*No call sites found*


---

CodeBookLink.render()
src/codebook/parser.py:51
*No call sites found*

</cicada>
```

**Parameters:**
- `function_name` (required) - Function name to search
- `module_name` (optional) - Limit to specific module

### search-module

Search for modules:

```html
<cicada endpoint="search-module" module_name="CodeBookParser">
{
  "module": "CodeBookParser",
  "location": "src/codebook/parser.py:75",
  "moduledoc": "```python\nclass CodeBookParser:\n```\nParser for extracting and manipulating codebook links in markdown.\n\nSupported formats:\n1. \\[`VALUE`\\](codebook:TEMPLATE) - inline value display\n2. [text](URL \"codebook:TEMPLATE\") - URL that gets updated\n3. &lt;span data-codebook=\"TEMPLATE\"&gt;VALUE&lt;/span&gt; - inline HTML\n4. &lt;div data-codebook=\"TEMPLATE\"&gt;CONTENT&lt;/div&gt; - multiline HTML",
  "counts": {
    "public": 9,
    "private": 0
  },
  "functions": [
    {
      "signature": "def count_links(\n  self,\n  content: str\n) -> int:",
      "line": 260,
      "type": "public"
    },
    {
      "signature": "def div_replacer(\n  match: re.Match[str]\n) -> str:",
      "line": 232,
      "type": "public"
    },
    {
      "signature": "def find_links(\n  self,\n  content: str\n) -> Iterator[CodeBookLink]:",
      "line": 105,
      "type": "public"
    },
    {
      "signature": "def find_templates(\n  self,\n  content: str\n) -> list[str]:",
      "line": 171,
      "type": "public"
    },
    {
      "signature": "def has_codebook_links(\n  self,\n  content: str\n) -> bool:",
      "line": 243,
      "type": "public"
    },
    {
      "signature": "def inline_replacer(\n  match: re.Match[str]\n) -> str:",
      "line": 201,
      "type": "public"
    },
    {
      "signature": "def replace_values(\n  self,\n  content: str,\n  values: dict[str, str]\n) -> str:",
      "line": 188,
      "type": "public"
    },
    {
      "signature": "def span_replacer(\n  match: re.Match[str]\n) -> str:",
      "line": 222,
      "type": "public"
    },
    {
      "signature": "def url_replacer(\n  match: re.Match[str]\n) -> str:",
      "line": 211,
      "type": "public"
    }
  ]
}
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

<cicada endpoint="search-function" function_name="get_codebook_version">
{
  "error": "Function not found",
  "query": "get_codebook_version",
  "hint": "Verify the function name spelling or try without arity"
}
</cicada>

### Markdown

Returns formatted markdown:

<cicada endpoint="search-function" function_name="get_codebook_version" format="markdown">
Not found: `get_codebook_version`. Try: `*get_codebook_version*` | query(['get', 'codebook', 'version'])
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
<cicada endpoint="search-function" function_name="render" jq=".results[*].location">
src/codebook/cli.py:108

src/codebook/parser.py:51
</cicada>
```

## JQ Path Syntax

Supported expressions:
- `.key` - Access object key
- `[0]` - Access array index
- `[*]` - Get all array elements
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

---

Rendered by CodeBook [`4f4a722`](codebook:codebook.version)
