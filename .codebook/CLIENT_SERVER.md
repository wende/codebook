# Client/Server Architecture

CodeBook uses a client/server architecture to separate markdown processing from data sources.

## Why the Split?

**Client (CodeBook CLI):** Parses markdown, finds `codebook:` links, updates files.

**Server (your backend):** Provides the actual values for templates.

This design keeps CodeBook generic. Your templates could come from anywhere:
- Code metrics from Cicada
- Database statistics
- Git information
- Custom business data
- External APIs

You implement the `/resolve` endpoint to return whatever values you need. CodeBook doesn't care what's behind it.

## Built-in Templates (Client-Side)

Templates starting with `codebook.` are resolved locally without contacting the server:

| Template | Description |
|----------|-------------|
| `codebook.version` | Git commit SHA or tag of current repo |

These work even without a backend configured.

## Mock Server

CodeBook includes a mock server for testing at `examples/mock_server.py`:

```bash
python examples/mock_server.py --port 3000
```

It provides sample templates (all prefixed with `server.`):

| Template | Example Value |
|----------|---------------|
| `server.SCIP.language_count` | `13` |
| `server.metrics.files_indexed` | `1000` |
| `server.project.name` | `CICADA` |
| `server.project.version` | `1.2.3` |
| `server.stats.total_users` | `42` |
| `server.API.endpoint_count` | `127` |
| `server.CI.build_status` | `Passing` |

The mock server also supports runtime updates via PUT/DELETE for testing dynamic values.

## API Contract

Your backend must implement:

### Single Resolution

```
GET /resolve/server.metrics.files_indexed
Response: {"value": "1000"}
```

### Batch Resolution (Optional)

```
POST /resolve/batch
Body: {"templates": ["server.metrics.files_indexed", "server.project.name"]}
Response: {"values": {"server.metrics.files_indexed": "1000", "server.project.name": "CICADA"}}
```

**Why POST for batch?** GET requests pass data in the URL, which has length limits (~2000-8000 chars). With many templates, the URL could exceed these limits. POST sends the list in the request body with no size constraints.

### Health Check

```
GET /health
Response: 200 OK
```

## Error Handling

When the server is unreachable or returns an error:

- **Server templates fail silently** - values stay unchanged in markdown
- **Built-in templates still work** - `codebook.*` are resolved locally
- **Warning is printed** - CLI logs that the server couldn't be reached

This means your documentation remains valid (with stale values) rather than breaking entirely.

## Configuration

Set your backend URL in `codebook.yml`:

```yaml
base_url: http://localhost:3000
```

Or via environment variable:

```bash
export CODEBOOK_BASE_URL=http://localhost:3000
```

---

See also: [Configuration](CONFIGURATION.md) | [Templates](TEMPLATES.md)

Rendered by CodeBook [`3d86e3c`](codebook:codebook.version)
