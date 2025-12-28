# Backlink Deduplication

## Problem

When rendering the same source file multiple times, backlinks could be added multiple times to the target:

```markdown
--- BACKLINKS ---
[SOURCE](source.md "codebook:backlink")
[SOURCE](source.md "codebook:backlink")  # Duplicate!
```

## Solution

The renderer uses regex pattern matching to detect existing backlinks before adding new ones. Backlinks are identified by **source filename** in the URL, not by link text.

### Detection Method

Uses a regex pattern to find backlinks pointing to the same source file:

```python
# Pattern matches any backlink pointing to this source file
backlink_pattern = rf'\[[^\]]*\]\([^)]*{re.escape(source_name)} "codebook:backlink"\)'
```

### Behavior

1. **New backlink**: If no backlink from this source exists, add it
2. **Exact match**: If backlink exists with same format, skip (no change)
3. **Format differs**: If backlink exists but format changed, replace it with new format

This ensures backlinks stay up-to-date when the format changes (e.g., when link text switches from original link text to source filename).

## Edge Cases

### Multiple files with same name

If `docs/README.md` and `api/README.md` both link to a target:

```markdown
--- BACKLINKS ---
[README](docs/README.md "codebook:backlink")
[README](api/README.md "codebook:backlink")
```

Both are kept because the full paths differ.

### Backlink in code block

Backlinks inside code blocks are ignored:

````markdown
```markdown
[SOURCE](source.md "codebook:backlink")  # Not a real backlink
```
````

The parser strips code blocks before checking for existing backlinks.

### Orphaned backlinks

When a source file no longer links to a target, the backlink is automatically removed during cleanup. See `_cleanup_orphaned_backlinks()`.

## Code Location

- `src/codebook/renderer.py:_update_backlinks()`
- `src/codebook/renderer.py:_cleanup_orphaned_backlinks()`

--- BACKLINKS ---
[README](README.md "codebook:backlink")
