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

Found 42 match(es) (showing private functions, showing partial name matches):

---

_file_conftest.renderer()
conftest.py:34
*No call sites found*


---

TestCLI.test_render_help()
test_cli.py:37
*No call sites found*


---

TestCLI.test_render_requires_directory()
test_cli.py:58
*No call sites found*


---

TestCLI.test_render_with_directory()
test_cli.py:64
*No call sites found*


---

TestCLI.test_render_dry_run()
test_cli.py:82
*No call sites found*


---

TestCLI.test_render_reports_statistics()
test_cli.py:99
*No call sites found*


---

TestCLI.test_render_non_recursive()
test_cli.py:117
*No call sites found*


---

TestCodeBookDiffer.mock_renderer()
test_differ.py:51
*No call sites found*


---

TestCodeBookDiffer.test_show_rendered_returns_rendered_content()
test_differ.py:200
*No call sites found*


---

TestCodeBookDiffer.test_show_rendered_returns_none_on_error()
test_differ.py:219
*No call sites found*


---

TestCodeBookDiffer.render_side_effect()
test_differ.py:278
*No call sites found*


---

TestCodeBookLink.test_render_generates_correct_link()
test_parser.py:11
*No call sites found*


---

TestCodeBookLink.test_render_handles_empty_value()
test_parser.py:25
*No call sites found*


---

TestCodeBookLink.test_render_handles_special_characters()
test_parser.py:39
*No call sites found*


---

TestBacklinks.test_render_markdown_link()
test_parser.py:508
*No call sites found*


---

TestBacklinks.test_render_backlink()
test_parser.py:526
*No call sites found*


---

TestCodeBookRenderer.renderer()
test_renderer.py:39
*No call sites found*


---

TestCodeBookRenderer.test_render_file_finds_templates()
test_renderer.py:43
*No call sites found*


---

TestCodeBookRenderer.test_render_file_updates_values()
test_renderer.py:59
*No call sites found*


---

TestCodeBookRenderer.test_render_file_dry_run_does_not_modify()
test_renderer.py:76
*No call sites found*


---

TestCodeBookRenderer.test_render_file_handles_no_links()
test_renderer.py:92
*No call sites found*


---

TestCodeBookRenderer.test_render_file_handles_read_error()
test_renderer.py:108
*No call sites found*


---

TestCodeBookRenderer.test_render_file_handles_write_error()
test_renderer.py:121
*No call sites found*


---

TestCodeBookRenderer.test_render_file_handles_unresolved_templates()
test_renderer.py:143
*No call sites found*


---

TestCodeBookRenderer.test_render_file_partial_resolution()
test_renderer.py:161
*No call sites found*


---

TestCodeBookRenderer.test_render_directory_processes_all_md_files()
test_renderer.py:179
*No call sites found*


---

TestCodeBookRenderer.test_render_directory_recursive()
test_renderer.py:195
*No call sites found*


---

TestCodeBookRenderer.test_render_directory_non_recursive()
test_renderer.py:212
*No call sites found*


---

TestCodeBookRenderer.test_render_directory_handles_invalid_path()
test_renderer.py:229
*No call sites found*


---

TestCodeBookRenderer.test_render_content_returns_rendered_content()
test_renderer.py:244
*No call sites found*


---

TestCodeBookRenderer.test_render_content_handles_no_links()
test_renderer.py:258
*No call sites found*


---

TestCodeBookRenderer.test_render_content_handles_no_resolved_values()
test_renderer.py:272
*No call sites found*


---

TestCodeBookRenderer.test_render_preserves_surrounding_content()
test_renderer.py:286
*No call sites found*


---

TestBacklinkUpdates.renderer()
test_renderer.py:324
*No call sites found*


---

TestBacklinkUpdates.test_render_finds_markdown_links()
test_renderer.py:328
*No call sites found*


---

TestBacklinkUpdates.test_render_creates_backlink_in_target()
test_renderer.py:341
*No call sites found*


---

TestBacklinkUpdates.test_render_appends_to_existing_backlinks()
test_renderer.py:359
*No call sites found*


---

TestBacklinkUpdates.test_render_does_not_duplicate_backlinks()
test_renderer.py:379
*No call sites found*


---

TestBacklinkUpdates.test_render_result_tracks_backlink_counts()
test_renderer.py:452
*No call sites found*


---

TestCodeBookWatcher.mock_renderer()
test_watcher.py:122
*No call sites found*


---

TestCodeBookWatcher.test_file_change_triggers_render()
test_watcher.py:190
*No call sites found*


---

TestCodeBookWatcher.test_on_render_callback_called()
test_watcher.py:213
*No call sites found*

</cicada>
```

**Parameters:**
- `function_name` (required) - Function name to search
- `module_name` (optional) - Limit to specific module

### search-module

Search for modules:

```html
<cicada endpoint="search-module" module_name="CodeBookParser" jq=".module,.location">
[
  null,
  null
]
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
  "error": "Function not found",
  "query": "get_codebook_version",
  "hint": "Verify the function name spelling or try without arity"
}
```
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
42
</cicada>
```

### Extract nested value

```html
<cicada endpoint="search-function" function_name="render" jq=".results[0].module">
_file_conftest
</cicada>
```

### Extract array of values

```html
<cicada endpoint="search-function" function_name="render" jq=".results[*].location">

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
def test_render_file_finds_templates(
  self,
  renderer: CodeBookRenderer,
  mock_client: MagicMock,
  temp_dir: Path
): # -> None:
</cicada>

---

Rendered by CodeBook [`6742eaf`](codebook:codebook.version)

--- BACKLINKS ---
[Cicada Integration](README.md "codebook:backlink")
