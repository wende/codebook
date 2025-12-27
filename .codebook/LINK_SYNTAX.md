# Link Syntax Reference

CodeBook supports multiple syntax formats for embedding dynamic values in markdown.

## 1. Inline Links

The primary format for inline values:

```markdown
[`VALUE`](codebook:TEMPLATE)
```

**Example:**
```markdown
The project has [`1000`](codebook:metrics.files_indexed) files indexed.
```

**Renders as:** The project has [`1000`](codebook:metrics.files_indexed) files indexed.

## 2. Codebook Elements

For inline HTML contexts:

```html
<codebook file="TEMPLATE">VALUE</codebook>
<codebook file="examples.config">
server:
  port: 3000
</codebook>
```

**Example:**
```html
Project: <codebook file="project.name">CICADA</codebook>
```

**Renders as:** Project: <codebook file="project.name">CICADA</codebook>

## 3. URL Links

Dynamic URLs with static link text:

```markdown
[Link Text](URL "codebook:TEMPLATE")
```

**Example:**
```markdown
[View Docs](https://example.com "codebook:API.docs_url")
```

The URL gets replaced while the link text stays the same.

## Special Templates

Use <codebook:TEMPLATES> to list all available templates.

### codebook.version

Returns the current CodeBook version (git tag/SHA):

```markdown
[`ee158b4`](codebook:codebook.version)
```

**Current version:** [`ee158b4`](codebook:codebook.version)

## Template Resolution

Templates are resolved via HTTP:

1. **Single:** `GET /resolve/{template}` → `{"value": "..."}`
2. **Batch:** `POST /resolve/batch` → `{"values": {...}}`

Results are cached based on the `cache_ttl` setting.

---

Rendered by CodeBook [`ee158b4`](codebook:codebook.version)
