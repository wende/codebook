# Frontmatter

CodeBook supports YAML frontmatter in markdown files. Frontmatter must appear at the very beginning of the file, enclosed by `---` delimiters.

## Syntax

```markdown
---
title: My Title
tags: [tag1, tag2]
disable: [links, backlinks]
---

# Document content starts here
```

## Supported Fields

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Document title (for metadata/indexing) |
| `tags` | string or array | Tags for categorizing the document |
| `disable` | string or array | Features to disable for this file |

## Disable Options

The `disable` field accepts the following values:

- `links` - Disables all CodeBook link processing (templates, exec blocks, cicada queries)
- `backlinks` - Disables automatic backlink generation to other documents

## Examples

### Disable all link processing

```markdown
---
disable: links
---

This file will not have any codebook links processed.
[`value`](codebook:template) will remain unchanged.
```

### Disable only backlinks

```markdown
---
disable: backlinks
---

Links like [`value`](codebook:template) will still be resolved,
but [Other Doc](other.md) won't generate a backlink in other.md.
```

### Multiple tags

```markdown
---
title: API Reference
tags: [api, reference, v2]
---
```

### Single values as strings

Both array and string syntax work for single values:

```markdown
---
tags: documentation
disable: backlinks
---
```

## Notes

- Frontmatter is optional
- Invalid YAML is silently ignored (file processes normally)
- Custom fields are preserved in the `raw` property for programmatic access
- Frontmatter that doesn't start at line 1 is not recognized

--- BACKLINKS ---
[Frontmatter](README.md "codebook:backlink")
