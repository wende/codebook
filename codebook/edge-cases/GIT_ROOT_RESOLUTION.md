# Git Root Resolution

## Problem

CodeBook needs to resolve paths relative to the git repository root for:

1. **Diff generation** - Compare against git refs
2. **Backlinks** - Support absolute paths like `/docs/api.md`
3. **Version resolution** - Get `codebook.version` from git

## Solution

The differ and renderer use `git rev-parse --show-toplevel`:

```python
def _get_git_root(self, path: Path) -> Path | None:
    """Find git repository root for a path."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path if path.is_dir() else path.parent,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except Exception:
        pass
    return None
```

## Use Cases

### Diff Generation

```python
# Get relative path from git root
git_root = self._get_git_root(file_path)
rel_path = file_path.relative_to(git_root)

# Compare with git ref
git_content = subprocess.run(
    ["git", "show", f"{ref}:{rel_path}"],
    cwd=git_root,
    ...
)
```

### Absolute Path Backlinks

When a link uses an absolute path:

```markdown
See [API Docs](/docs/api.md) for details.
```

The path `/docs/api.md` is resolved relative to git root:

```python
if link_path.startswith('/'):
    git_root = self._get_git_root(source_file)
    target = git_root / link_path[1:]  # Remove leading /
```

### Version Resolution

```python
def get_codebook_version() -> str:
    # Try getting tag
    result = subprocess.run(
        ["git", "describe", "--tags", "--always"],
        capture_output=True, text=True
    )
    return result.stdout.strip()
```

## Edge Cases

### Not a git repository

If `git rev-parse` fails:
- Returns `None`
- Diff generation fails gracefully
- Absolute paths won't resolve
- Version returns "unknown"

### Nested git repositories

If a file is in a nested git repo:
- Uses the innermost repository
- This is usually the desired behavior

### Worktrees

Git worktrees are handled correctly:
- `--show-toplevel` returns worktree root
- Not the main repository

### Submodules

In a submodule:
- Returns submodule root
- Not parent repository root

## Code Location

- `src/codebook/differ.py:_get_git_root()`
- `src/codebook/renderer.py:get_codebook_version()`
- `src/codebook/renderer.py:_update_backlinks()`

---

Rendered by CodeBook

--- BACKLINKS ---
[README](README.md "codebook:backlink")
