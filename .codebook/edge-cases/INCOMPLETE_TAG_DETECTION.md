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
   <cicada endpoint="query"
   <!-- No closing > yet -->
   ```

2. **Unclosed quotes** in attributes:
   ```html
   <exec lang="python
   <!-- Quote not closed -->
   ```

3. **Missing closing tags**:
   ```html
   <exec lang="python">
   print("hello")
   <!-- No </exec> yet -->
   ```

### Tag Types Detected

- `<cicada ...>`
- `<exec ...>`
- `<div data-codebook="...">`
- `<span data-codebook="...">`

## Watcher Behavior

When `has_incomplete_tags()` returns `True`:

1. The watcher **skips** rendering that file
2. No error is shown to the user
3. The file will be re-rendered when complete

## Code Location

- `src/codebook/parser.py:has_incomplete_tags()`
- `src/codebook/watcher.py` - Uses this check before rendering

## Testing

```python
# Returns True - incomplete
parser.has_incomplete_tags('<cicada endpoint="query"')

# Returns False - complete
parser.has_incomplete_tags('<cicada endpoint="query">result</cicada>')
```

---

Rendered by CodeBook
