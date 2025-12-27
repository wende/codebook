# Edge Cases & Implementation Details

This folder documents implementation-specific behaviors that are important to understand but don't warrant full documentation sections.

## Contents

- **[Incomplete Tag Detection](INCOMPLETE_TAG_DETECTION.md)** - How the watcher handles partially-written tags
- **[Render Cooldown](RENDER_COOLDOWN.md)** - Preventing infinite render loops
- **[ANSI Escape Stripping](ANSI_ESCAPE_STRIPPING.md)** - Cleaning error output from Jupyter
- **[Task Version Diff Skipping](TASK_VERSION_DIFF_SKIPPING.md)** - Filtering version-only changes
- **[Backlink Deduplication](BACKLINK_DEDUPLICATION.md)** - How duplicate backlinks are handled
- **[Cache Expiration](CACHE_EXPIRATION.md)** - TTL-based cache behavior
- **[Batch Resolution Fallback](BATCH_RESOLUTION_FALLBACK.md)** - Graceful degradation when batch fails
- **[Git Root Resolution](GIT_ROOT_RESOLUTION.md)** - Finding repository root for paths

---

Rendered by CodeBook
