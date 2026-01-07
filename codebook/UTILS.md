## Utility Commands

The `codebook utils` command group provides helper utilities for managing and inspecting your CodeBook environment.

### Status

```bash
codebook utils status
```

**Purpose:** Provides a comprehensive health check and overview of your CodeBook documentation environment.

**Output includes:**

1. **Task Statistics**
   - Total number of tasks in the tasks directory
   - Breakdown by status (if tasks have status metadata)
   - Recently created/modified tasks

2. **Link Health**

   Validates different types of links based on their nature:

   **File References** - `[text](file.md)` or `[text](file.md#section)`
   - Check if target file exists
   - For section links (`#section`), verify the heading exists in the target file
   - Report broken links with source file and line number
   - Report broken section anchors with expected heading

   **CodeBook Templates** - `` [`value`](codebook:template) ``
   - Count total templates found
   - Optionally verify backend connectivity

   **EXEC Blocks** - `<exec lang="python">code</exec>`
   - Validate language is supported (currently: `python`)
   - Check Python syntax with `ast.parse()` (no execution)
   - Verify Jupyter kernel is available
   - Report syntax errors with file and line number

   **CICADA Blocks** - `<cicada endpoint="query" param="value">...</cicada>`
   - Validate endpoint name (`query`, `search-function`, `search-module`, `git-history`, `expand-result`, `refresh-index`, `query-jq`)
   - Check required parameters are present for each endpoint type
   - Optionally verify Cicada server connectivity
   - Report invalid endpoints/params with file and line number

3. **Backend Connectivity**
   - Backend server health status (if configured)
   - URL and response time

4. **Cicada Integration**
   - Cicada server status (if configured)
   - Index availability

**Exit codes:**
- `0` - All checks passed
- `1` - Warnings found (broken links, missing files)
- `2` - Errors found (backend unreachable, critical failures)

--- BACKLINKS ---
[README](README.md "codebook:backlink")
