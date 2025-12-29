This file is a diff of a feature specification. I want you to change the code to match the new spec.

# Backlinks names

<diff file="codebook/SYNTAX.md">
```diff
diff --git a/codebook/SYNTAX.md b/codebook/SYNTAX.md
index d2b663f..8d42f31 100644
--- a/codebook/SYNTAX.md
+++ b/codebook/SYNTAX.md
@@ -59,15 +59,18 @@ Standard markdown links to other `.md` files trigger automatic backlink generati
 [API Documentation](api.md)
 ```
 
-When rendered, `api.md` will automatically have a backlink added:
+When rendered, `api.md` will automatically have a backlink added using the source file name:
 
 ```markdown
 --- BACKLINKS ---
-[API Documentation](source.md "codebook:backlink")
+[source](source.md "codebook:backlink")
 ```
 
 **Features:**
+- Backlink text uses source file name (not original link text)
 - Automatic deduplication (won't create duplicate backlinks)
+- Existing backlinks are updated if format changes
+- Orphaned backlinks are automatically removed when source no longer links
 - Relative path calculation
 - Creates `--- BACKLINKS ---` section if needed
 - Can be disabled via frontmatter: `disable: backlinks`
@@ -76,8 +79,6 @@ When rendered, `api.md` will automatically have a backlink added:
 
 See also: [Templates](TEMPLATES.md)
 
-Rendered by CodeBook [`v0.1.0-5-g018d023`](codebook:codebook.version)
-
 --- BACKLINKS ---
-[Syntax](TEMPLATES.md "codebook:backlink")
-[Syntax](README.md "codebook:backlink")
+[TEMPLATES](TEMPLATES.md "codebook:backlink")
+[README](README.md "codebook:backlink")
```
</diff>

---
After completing the task, please update the task file with:
- Description of the feature task that was requested
- Short description of the changes that were made and why
Include implemenentation details how the task was implemented.
Do not include code snippets. Only describe the functional changes that were made.
Do not remove diff lines from the task file.
--- FEATURE TASK ---
Change backlink text to use source file name instead of original link text, and add cleanup logic to remove orphaned backlinks.

--- NOTES ---
Previously, backlinks used the link text from the original markdown link (e.g., `[API Documentation]`). This was confusing because you couldn't tell which file the backlink came from.

--- SOLUTION ---
1. **Backlink text now uses source file name**: In `_update_backlinks`, changed from `link.extra` (original link text) to `source_path.stem` (file name without extension). Backlinks now display as `[README](README.md ...)` instead of `[Some Link Text](README.md ...)`.

2. **Existing backlinks are updated**: Modified the deduplication logic to detect existing backlinks pointing to the same source file (using regex pattern) and replace them with the new format instead of skipping.

3. **Orphaned backlink cleanup**: Added `_cleanup_orphaned_backlinks` method that runs after rendering each file. For each backlink in a file's BACKLINKS section, it checks if the source file actually still links to this file. If not, the backlink is removed.

4. **Footer removed from SYNTAX.md**: As per the spec diff, removed the `Rendered by CodeBook` footer line.

5. **Task diff format changed**: Wrapped diffs in `<diff file="path">...</diff>` tags to make parsing unambiguous. Previously, diffs used only markdown code fences which broke when the diff content itself contained code fences. The new format allows `task update` to reliably find and replace existing diffs.

--- REVIEW 202512281830 ---
**Documentation Accuracy: EXCELLENT**

The SYNTAX.md documentation accurately describes all the implemented changes:

✓ **Backlink text uses source file name**: Correctly documented that backlinks now use the source filename (e.g., `[source](source.md)`) instead of original link text. Implementation uses `source_path.stem` at line 437 in renderer.py.

✓ **Existing backlinks updated**: Documentation correctly states that existing backlinks are updated if format changes. The implementation at lines 503-514 uses regex pattern matching to find and replace backlinks from the same source file with the new format.

✓ **Orphaned backlinks cleanup**: Accurately documented that backlinks are removed when the source no longer links. The `_cleanup_orphaned_backlinks` method (lines 544-634) verifies each backlink's source file still contains a valid link and removes orphaned ones.

✓ **Frontmatter disable**: Documentation correctly notes backlinks can be disabled via `disable: backlinks` frontmatter. Implementation checks `frontmatter.backlinks_disabled` at lines 216 and 221.

✓ **Relative path calculation**: Documented feature is implemented at lines 472-485 with git root resolution for absolute paths.

✓ **BACKLINKS section creation**: Documented automatic section creation is implemented at lines 523-532.

✓ **Deduplication**: Documented automatic deduplication is implemented (lines 507-522) though the documentation could be clearer that deduplication is now filename-based rather than full-entry-based.

**Minor Observations:**
- The BACKLINK_DEDUPLICATION.md edge case file still references the old deduplication logic and should be updated to reflect the new filename-based approach and backlink format.
- The SOLUTION description in this task file is comprehensive and accurately reflects the implementation.

--- REVIEW 202512281900 ---
I have verified the changes in `codebook/SYNTAX.md` and the implementation in `src/codebook/renderer.py`.

**Documentation vs Implementation:**
The documentation in `codebook/SYNTAX.md` accurately describes the new functionality.
- **Backlink Naming**: The documentation states backlinks use the source file name. The implementation in `renderer.py` (`link_text = source_path.stem`) matches this.
- **Cleanup**: The documentation mentions orphaned backlink removal. `renderer.py` has a `_cleanup_orphaned_backlinks` method that logic matches the description.
- **Updates**: The documentation says existing backlinks are updated. The code attempts to find existing backlinks by source filename and replaces them if the format differs.

**Additional Notes:**
- As noted in the previous review, `codebook/edge-cases/BACKLINK_DEDUPLICATION.md` contains pseudo-code (`_get_existing_backlinks`) that does not exist in the current codebase and should be updated to match the regex-based approach in `_update_backlinks`.