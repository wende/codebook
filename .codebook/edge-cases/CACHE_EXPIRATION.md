# Cache Expiration

## Overview

CodeBook uses TTL (Time-To-Live) based caching for template resolution to reduce HTTP requests.

## Cache Structure

```python
@dataclass
class CacheEntry:
    value: str
    expires_at: float  # Unix timestamp
```

Each cached value has an individual expiration time.

## Configuration

```bash
# CLI
codebook render docs/ --cache-ttl 60

# Config file
cache_ttl: 60.0  # seconds, 0 to disable
```

## Behavior

### On Cache Hit

```python
def resolve(self, template: str) -> str | None:
    if template in self._cache:
        entry = self._cache[template]
        if time.time() < entry.expires_at:
            return entry.value  # Use cached value
        # Expired, continue to fetch
```

### On Cache Miss or Expiration

1. Make HTTP request to backend
2. Store result with new expiration: `time.time() + cache_ttl`
3. Return value

### Cache Disabled (TTL = 0)

When `cache_ttl` is 0:
- No values are cached
- Every resolution makes an HTTP request
- Useful for debugging or real-time data

## Batch Resolution Caching

When using batch resolution, all returned values are cached:

```python
def resolve_batch(self, templates: list[str]) -> dict:
    # Check cache first for each template
    uncached = [t for t in templates if not self._is_cached(t)]

    # Fetch uncached templates
    results = self._batch_request(uncached)

    # Cache all results
    for template, value in results.items():
        self._cache[template] = CacheEntry(
            value=value,
            expires_at=time.time() + self.cache_ttl
        )
```

## Cache Clearing

Manual cache clearing:

```bash
codebook clear-cache
```

Programmatic:

```python
client.clear_cache()  # Clears all entries
```

## Edge Cases

### Stale data

If backend data changes during cache lifetime:
- Old value returned until expiration
- Solution: Lower TTL or clear cache manually

### Memory usage

Cache grows unbounded during long sessions:
- Each unique template adds an entry
- No automatic cleanup of expired entries
- Clearing cache frees all memory

### Per-process cache

The cache is in-memory per process:
- Not shared between `codebook` invocations
- File watcher maintains cache across renders
- CI runs start with empty cache

## Code Location

- `src/codebook/client.py:CodeBookClient`
- `src/codebook/client.py:CacheEntry`

---

Rendered by CodeBook
