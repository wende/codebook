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

## 2. HTML Elements

For inline and multiline HTML contexts:

```html
<codebook file="TEMPLATE">VALUE</codebook>
<codebook file="examples.config">
server:
  port: 3000
</codebook>
```

**Example:**
```html
Project: <span data-codebook="project.name">CICADA</span>
```

**Renders as:** Project: <span data-codebook="project.name">CICADA</span>

## 3. URL Links

Dynamic URLs with static link text:

```markdown
[Link Text](URL "codebook:TEMPLATE")
```

**Example:**
```markdown
[View Docs](URL "codebook:API.docs_url")
```

The URL gets replaced while the link text stays the same.

## 4. Markdown Links & Backlinks

Standard markdown links to other `.md` files trigger automatic backlink generation:

```markdown
[API Documentation](api.md)
```

When rendered, `api.md` will automatically have a backlink added:

```markdown
--- BACKLINKS ---
[API Documentation](source.md "codebook:backlink")
```

**Features:**
- Automatic deduplication (won't create duplicate backlinks)
- Relative path calculation
- Creates `--- BACKLINKS ---` section if needed
- Can be disabled via frontmatter: `disable: backlinks`

## Special Templates

Use <codebook:TEMPLATES> to list all available templates.

### codebook.version

Returns the current CodeBook version (git tag/SHA):

```markdown
[`08bb5c1`](codebook:codebook.version)
```

**Current version:** [`08bb5c1`](codebook:codebook.version)

## Template Resolution

Templates are resolved via HTTP:

1. **Single:** `GET /resolve/{template}` → `{"value": "..."}`
2. **Batch:** `POST /resolve/batch` → `{"values": {...}}`

Results are cached based on the `cache_ttl` setting.

---

Rendered by CodeBook [`08bb5c1`](codebook:codebook.version)

--- BACKLINKS ---
[Link Syntax](README.md "codebook:backlink")
