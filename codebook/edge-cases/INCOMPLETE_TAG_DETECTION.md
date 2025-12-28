# Incomplete Tag Detection

## Problem

When a user is typing a new `<exec>`, `<cicada>`, or other codebook tag, the file watcher may trigger a render while the tag is incomplete. This could cause:

1. Parse errors
2. Partial content being processed
3. Lost user input

## Solution

The parser includes `has_incomplete_tags()` which detects partially-written tags:

```python
def has_incomplete_tags(self, content: str) -> bool:
    """Check if content has incomplete/partially-written tags."""
```

### Detection Patterns

The method looks for:

1. **Missing closing `>`** in tag opening:
   ```html
   <cicada endpoint="query">
Error: 422 Client Error: Unprocessable Content for url: http://localhost:9999/api/query
</cicada>')
```

---

Rendered by CodeBook

--- BACKLINKS ---
[README](README.md "codebook:backlink")
