# Templates Reference

Templates are dynamic values embedded in markdown using the `codebook:` prefix.

## Built-in Templates

These templates are resolved **locally by the CLI** - no server required.

| Template | Description |
|----------|-------------|
| `codebook.version` | Current git commit SHA or tag |

**Example:**
```markdown
[`v0.1.1-6-gaedc06c`](codebook:codebook.version)
```

**Current version:** [`v0.1.1-6-gaedc06c`](codebook:codebook.version)

## Server Templates

Templates starting with `server.` are resolved via HTTP from your backend service.

Use `<codebook:TEMPLATES>` to list available templates from your backend.

**Example:**
```markdown
[`1000`](codebook:server.metrics.files_indexed)
```

**Common patterns:**
- `server.metrics.*` - Custom metrics
- `server.project.*` - Project configuration
- `server.API.*` - API statistics

See [Client/Server Architecture](CLIENT_SERVER.md) for how to implement a backend.

## Resolution Order

1. `codebook.*` → resolved locally (no server needed)
2. `server.*` → HTTP call to backend
3. Other prefixes → ignored

Results from the backend are cached based on the `cache_ttl` setting.

---

See also: [Syntax](SYNTAX.md) | [Client/Server](CLIENT_SERVER.md)

--- BACKLINKS ---
[SYNTAX](SYNTAX.md "codebook:backlink")
[README](README.md "codebook:backlink")
[CLIENT_SERVER](CLIENT_SERVER.md "codebook:backlink")
