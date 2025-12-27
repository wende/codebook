# Batch Resolution Fallback

## Overview

CodeBook supports batch resolution of multiple templates in a single HTTP request. When batch fails, it gracefully falls back to individual requests.

## Batch Endpoint

```
POST /resolve/batch
Body: {"templates": ["template1", "template2", "template3"]}
Response: {"values": {"template1": "value1", "template2": "value2", ...}}
```

## Fallback Flow

```
1. Try batch endpoint
   ↓ (fails: 404, 500, timeout, etc.)
2. Fall back to individual GET requests
   GET /resolve/template1
   GET /resolve/template2
   GET /resolve/template3
```

## Implementation

```python
def resolve_batch(self, templates: list[str]) -> dict[str, str]:
    # Step 1: Check cache
    cached = {}
    uncached = []
    for t in templates:
        if self._is_cached(t):
            cached[t] = self._cache[t].value
        else:
            uncached.append(t)

    if not uncached:
        return cached

    # Step 2: Try batch
    batch_result = self._resolve_batch_endpoint(uncached)
    if batch_result is not None:
        return {**cached, **batch_result}

    # Step 3: Fall back to individual
    individual = {}
    for t in uncached:
        value = self._resolve_single(t)
        if value is not None:
            individual[t] = value

    return {**cached, **individual}
```

## When Batch Fails

The batch endpoint fails if:

1. **404 Not Found** - Endpoint doesn't exist
2. **500 Server Error** - Backend error
3. **Timeout** - Request takes too long
4. **Invalid response** - Not JSON or missing `values` key
5. **Network error** - Connection refused, DNS failure

## Performance Implications

### Batch available (optimal)
- 1 HTTP request for N templates
- Lowest latency

### Batch unavailable (fallback)
- N HTTP requests for N templates
- Higher latency, but still works

### Cached (best)
- 0 HTTP requests
- Instant response

## Backend Implementation Note

If your backend doesn't need batch support:
- Don't implement `/resolve/batch`
- CodeBook will automatically use individual requests
- No configuration needed

## Partial batch results

If batch returns only some values:

```json
// Request
{"templates": ["a", "b", "c"]}

// Response (missing "c")
{"values": {"a": "1", "b": "2"}}
```

CodeBook:
- Uses batch results for "a" and "b"
- Does NOT fall back for "c" (assumes intentionally missing)
- Returns partial results

## Code Location

- `src/codebook/client.py:resolve_batch()`
- `src/codebook/client.py:_resolve_batch_endpoint()`

---

Rendered by CodeBook
