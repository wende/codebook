# Backlink Deduplication

## Problem

When rendering the same source file multiple times, backlinks could be added multiple times to the target:

```markdown
--- BACKLINKS ---
[Link](source.md "codebook:backlink")
[Link](source.md "codebook:backlink")  # Duplicate!
[Link](source.md "codebook:backlink")  # Another duplicate!
```

## Solution

The renderer checks for existing backlinks before adding new ones:

```python
def _update_backlinks(self, source_path: Path, markdown_links: list) -> int:
    # Check if backlink already exists
    existing_backlinks = self._get_existing_backlinks(target_content)
    if source_filename in existing_backlinks:
        continue  # Skip, already linked
```

### Deduplication Key

Backlinks are deduplicated by **source filename**, not full path:

```markdown
# These are considered the same:
[Link](../docs/source.md "codebook:backlink")
[Link](source.md "codebook:backlink")
```

This handles cases where:
- Files are moved
- Relative paths change
- The same file is linked from different locations

### Detection Method

The method searches for the source filename in the BACKLINKS section:

```python
def _get_existing_backlinks(self, content: str) -> set[str]:
    """Extract set of filenames from existing backlinks."""
    # Looks for patterns like: [text](filename.md "codebook:backlink")
```

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
[Link](source.md "codebook:backlink")  # Not a real backlink
```
````

The parser strips code blocks before checking for existing backlinks.

## Code Location

- `src/codebook/renderer.py:_update_backlinks()`
- `src/codebook/renderer.py:_get_existing_backlinks()`

---

Rendered by CodeBook
