# Syntax Reference

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
[View Docs](URL "codebook:API.docs_url")
```

The URL gets replaced while the link text stays the same.

## 4. Markdown Links & Backlinks

Standard markdown links to other `.md` files trigger automatic backlink generation:

```markdown
[API Documentation](api.md)
```

When rendered, `api.md` will automatically have a backlink added using the source file name:

```markdown
--- BACKLINKS ---
[source](source.md "codebook:backlink")
```

**Features:**
- Backlink text uses source file name (not original link text)
- Automatic deduplication (won't create duplicate backlinks)
- Existing backlinks are updated if format changes
- Orphaned backlinks are automatically removed when source no longer links
- Relative path calculation
- Creates `--- BACKLINKS ---` section if needed
- Can be disabled via frontmatter: `disable: backlinks`

---

See also: [Templates](TEMPLATES.md)

--- BACKLINKS ---
[TEMPLATES](TEMPLATES.md "codebook:backlink")
[README](README.md "codebook:backlink")
