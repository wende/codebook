This file is a diff of a feature specification. I want you to change the code to match the new spec.

# Bidirectional links

```diff
diff --git a/.codebook/LINK_SYNTAX.md b/.codebook/LINK_SYNTAX.md
index 23a1bc1..ae7ee78 100644
--- a/.codebook/LINK_SYNTAX.md
+++ b/.codebook/LINK_SYNTAX.md
@@ -36,7 +36,23 @@ Project: <codebook file="project.name">CICADA</codebook>
 
 **Renders as:** Project: <codebook file="project.name">CICADA</codebook>
 
-## 3. URL Links
+## 3. Bidirectional Links
+
+Bidirectional links get automatically included in the footer of the linked file.
+
+**Example:**
+
+```markdown
+[Link Text](FILEURL "codebook:link")
+```
+
+** In the linked file:
+```markdown
+--- BACKLINKS ---
+[Link Text](FILEURL "codebook:backlink")
+```
+
+## 4. URL Links
 
 Dynamic URLs with static link text:
 
@@ -60,10 +76,10 @@ Use <codebook:TEMPLATES> to list all available templates.
 Returns the current CodeBook version (git tag/SHA):
 
 ```markdown
-[`026a01a`](codebook:codebook.version)
+[`026a01a`](codebook:codebook.version)
 ```
 
-**Current version:** [`026a01a`](codebook:codebook.version)
+**Current version:** [`026a01a`](codebook:codebook.version)
 
 ## Template Resolution
 
@@ -76,4 +92,4 @@ Results are cached based on the `cache_ttl` setting.
 
 ---
 
-Rendered by CodeBook [`026a01a`](codebook:codebook.version)
+Rendered by CodeBook [`026a01a`](codebook:codebook.version)
```

