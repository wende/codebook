# Render Cooldown

## Problem

When CodeBook renders a file, it modifies the file. The file watcher detects this modification and triggers another render. This creates an infinite loop:

```
render → file change → render → file change → ...
```

## Solution

The watcher implements a cooldown period after each render:

```python
RENDER_COOLDOWN = 2.0  # seconds
```

### How It Works

1. After rendering a file, the watcher records the timestamp
2. When a file change is detected, the watcher checks:
   - Was this file rendered within the last 2 seconds?
   - If yes, skip the render
3. This breaks the infinite loop while still allowing legitimate edits

### Implementation

```python
class DebouncedHandler:
    def __init__(self):
        self._last_render_time = {}  # path -> timestamp

    def should_skip_cooldown(self, path: str) -> bool:
        last_render = self._last_render_time.get(path)
        if last_render and time.time() - last_render < RENDER_COOLDOWN:
            return True
        return False
```

## Edge Cases

### User edits during cooldown

If a user makes a quick edit within 2 seconds of a render:
- The edit might be skipped on first detection
- The debounce mechanism will catch subsequent saves
- Worst case: user saves again after 2 seconds

### Multiple rapid edits

The debounce mechanism (separate from cooldown) handles rapid edits:
- Debounce delay: 0.5 seconds (configurable)
- Only the final state is rendered

## Configuration

The cooldown is currently hardcoded. The debounce delay is configurable:

```bash
codebook watch docs/ --debounce 1.0
```

## Code Location

- `src/codebook/watcher.py:RENDER_COOLDOWN`
- `src/codebook/watcher.py:DebouncedHandler`

---

Rendered by CodeBook

--- BACKLINKS ---
[README](README.md "codebook:backlink")
