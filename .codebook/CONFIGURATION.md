# Configuration

CodeBook can be configured via `codebook.yml` for zero-config startup.

## Quick Start

```bash
# Create default config
codebook init

# Run with config
codebook run
```

## Config File Location

CodeBook searches for `codebook.yml` or `codebook.yaml` in:
1. Current directory
2. Parent directories (up to 10 levels)

Or specify explicitly:
```bash
codebook run -c path/to/codebook.yml
```

## Full Configuration Reference

```yaml
# Directory to watch for markdown files
watch_dir: .

# Enable Python code execution
exec: true

# Watch subdirectories recursively
recursive: true

# HTTP request timeout (seconds)
timeout: 10.0

# Cache TTL for resolved values (seconds)
cache_ttl: 60.0

# Backend server configuration
backend:
  # Backend URL for template resolution
  url: http://localhost:3000

  # Port for mock server (if starting)
  port: 3000

  # Auto-start mock server
  start: true

# Cicada code exploration configuration
cicada:
  # Enable Cicada queries
  enabled: true

  # Cicada server URL
  url: http://localhost:9999

  # Port for Cicada (if starting)
  port: 9999

  # Auto-start Cicada server
  start: true
```

## Minimal Configuration

```yaml
watch_dir: docs
exec: true
cicada:
  enabled: true
```

## Example Configurations

### Documentation Project

```yaml
watch_dir: docs
exec: true
recursive: true
backend:
  url: https://api.myproject.com
  start: false
cicada:
  enabled: false
```

### Local Development

```yaml
watch_dir: .codebook
exec: true
backend:
  start: true
  port: 3000
cicada:
  enabled: true
  start: true
  port: 9999
```

### CI/CD Pipeline

```yaml
watch_dir: docs
exec: false  # Don't execute code in CI
recursive: true
timeout: 30.0
backend:
  url: $BACKEND_URL  # Use environment variable
  start: false
cicada:
  enabled: false
```

## CLI Options

All config values can be overridden via CLI:

```bash
# Override base URL
codebook -b http://custom:3000 run

# Override cicada URL
codebook --cicada-url http://custom:9999 run

# Override timeout
codebook -t 30 run
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CODEBOOK_BASE_URL` | Default backend URL |
| `CICADA_URL` | Default Cicada URL |

## Commands

### codebook init

Create a default `codebook.yml`:

```bash
codebook init
codebook init -o custom-config.yml
```

### codebook run

Run with configuration:

```bash
codebook run              # Use codebook.yml
codebook run -c other.yml # Use specific config
```

### codebook render

One-time render:

```bash
codebook render docs/
codebook render docs/ --exec --cicada
codebook render docs/ --dry-run
```

### codebook watch

Watch for changes:

```bash
codebook watch docs/
codebook watch docs/ --exec --cicada
```

---

Rendered by CodeBook [`4f4a722`](codebook:codebook.version)
