This file is a diff of a feature specification. I want you to change the code to match the new spec.

# Codebook Tags

```diff
diff --git a/.codebook/LINK_SYNTAX.md b/.codebook/LINK_SYNTAX.md
index a119bc5..23a1bc1 100644
--- a/.codebook/LINK_SYNTAX.md
+++ b/.codebook/LINK_SYNTAX.md
@@ -17,40 +17,26 @@ The project has [`1000`](codebook:metrics.files_indexed) files indexed.
 
 **Renders as:** The project has [`1000`](codebook:metrics.files_indexed) files indexed.
 
-## 2. Span Elements
+## 2. Codebook Elements
 
 For inline HTML contexts:
 
 ```html
-<span data-codebook="TEMPLATE">VALUE</span>
+<codebook file="TEMPLATE">VALUE</codebook>
+<codebook file="examples.config">
+server:
+  port: 3000
+</codebook>
 ```
 
 **Example:**
 ```html
-Project: <span data-codebook="project.name">CICADA</span>
-```
-
-**Renders as:** Project: <span data-codebook="project.name">CICADA</span>
-
-## 3. Div Elements
-
-For multiline content blocks:
-
-```html
-<div data-codebook="TEMPLATE">
-MULTILINE CONTENT
-</div>
+Project: <codebook file="project.name">CICADA</codebook>
 ```
 
-**Example:**
-```html
-<div data-codebook="examples.config">
-server:
-  port: 3000
-</div>
-```
+**Renders as:** Project: <codebook file="project.name">CICADA</codebook>
 
-## 4. URL Links
+## 3. URL Links
 
 Dynamic URLs with static link text:
 
@@ -67,15 +53,17 @@ The URL gets replaced while the link text stays the same.
 
 ## Special Templates
 
+Use <codebook:TEMPLATES> to list all available templates.
+
 ### codebook.version
 
 Returns the current CodeBook version (git tag/SHA):
 
 ```markdown
-[`026a01a`](codebook:codebook.version)
+[`026a01a`](codebook:codebook.version)
 ```
 
-**Current version:** [`026a01a`](codebook:codebook.version)
+**Current version:** [`026a01a`](codebook:codebook.version)
 
 ## Template Resolution
 
@@ -88,4 +76,4 @@ Results are cached based on the `cache_ttl` setting.
 
 ---
 
-Rendered by CodeBook [`026a01a`](codebook:codebook.version)
+Rendered by CodeBook [`026a01a`](codebook:codebook.version)
```

```diff
diff --git a/.codebook/TASKS.md b/.codebook/TASKS.md
index d4d6cee..3f01165 100644
--- a/.codebook/TASKS.md
+++ b/.codebook/TASKS.md
@@ -8,14 +8,14 @@ CodeBook includes a task management feature for capturing documentation changes.
 codebook task new "Title of the task" ./scope
 ```
 
-This creates `.codebook/tasks/YYYYMMDD-TITLE_OF_THE_TASK.md` containing git diffs for each modified file.
+This creates `.codebook/tasks/YYYYMMDDHHMM-TITLE_OF_THE_TASK.md` containing git diffs for each modified file.
 
 Users can delete the tasks by running `codebook task delete` with the "Title of the task" or without it the pick tool will be used to select the task to delete from the list of tasks.
 
 
 ## Behavior
 
-By default, `task new` only includes files that have uncommitted changes (staged or unstaged). Use `--all` to capture all files regardless of git status.
+By default, `task new` only includes files that have uncommitted changes (staged or unstaged).
 
 The title is converted to `UPPER_SNAKE_CASE` for the filename.
 And the task is prepended with a generic wrapper describing what to be changed.
@@ -66,4 +66,4 @@ diff --git a/path/to/file.md b/path/to/file.md
 
 ---
 
-Rendered by CodeBook [`026a01a`](codebook:codebook.version)
+Rendered by CodeBook [`026a01a`](codebook:codebook.version)
```

