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

## 2. Span Elements

For inline HTML contexts:

```html
<span data-codebook="TEMPLATE">VALUE</span>
```

**Example:**
```html
Project: <span data-codebook="project.name">CICADA</span>
```

**Renders as:** Project: <span data-codebook="project.name">CICADA</span>

## 3. Div Elements

For multiline content blocks:

```html
<div data-codebook="TEMPLATE">
MULTILINE CONTENT
</div>
```

**Example:**
```html
<div data-codebook="examples.config">
server:
  port: 3000
</div>
```

## 4. URL Links

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

### codebook.version

Returns the current CodeBook version (git tag/SHA):

```markdown
[`4f4a722`](codebook:codebook.version)
```

**Current version:** [`4f4a722`](codebook:codebook.version)

## Template Resolution

Templates are resolved via HTTP:

1. **Single:** `GET /resolve/{template}` → `{"value": "..."}`
2. **Batch:** `POST /resolve/batch` → `{"values": {...}}`

Results are cached based on the `cache_ttl` setting.

---

Rendered by CodeBook [`4f4a722`](codebook:codebook.version)
