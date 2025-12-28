This file is a diff of a feature specification. I want you to change the code to match the new spec.

# More configuration

```diff
diff --git a/.codebook/CONFIGURATION.md b/.codebook/CONFIGURATION.md
index 4c69e00..daf7c4b 100644
--- a/.codebook/CONFIGURATION.md
+++ b/.codebook/CONFIGURATION.md
@@ -26,9 +26,12 @@ codebook run -c path/to/codebook.yml
 ## Full Configuration Reference
 
 ```yaml
-# Directory to watch for markdown files
+# Directory to store specs, features and task files
 watch_dir: .
 
+# Directory containing tasks. Automatically ignored in watch and render commands.
+tasks_dir: .codebook/tasks
+
 # Enable Python code execution
 exec: true
 
@@ -182,4 +185,4 @@ codebook watch docs/ --exec --cicada
 
 ---
 
-Rendered by CodeBook [`026a01a`](codebook:codebook.version)
+Rendered by CodeBook [`026a01a`](codebook:codebook.version)
```

```diff
diff --git a/.codebook/README.md b/.codebook/README.md
index c49be94..59fc3d4 100644
--- a/.codebook/README.md
+++ b/.codebook/README.md
@@ -1,6 +1,9 @@
 # CodeBook Documentation
 
-Dynamic Markdown Documentation with Live Code References.
+Spec Driven Development framework.
+Document features in markdown in you `.codebook` directory.
+Each change can be turned into a task by running `codebook task new "Title of the task" ./scope` [Tasks](TASKS.md)
+These tasks are actionable pieces of work that can be fed to an AI agent to implement.
 
 ## Overview
 
@@ -28,7 +31,7 @@ codebook run
 | Metric    | Value                               |
 | --------- | ----------------------------------- |
 | Templates | [`42`](codebook:project.file_count) |
-| Version   | [`026a01a`](codebook:codebook.version)  |
+| Version   | [`026a01a`](codebook:codebook.version)  |
 
 ## Documentation Files
 
@@ -36,4 +39,4 @@ codebook run
 
 ---
 
-Rendered by CodeBook [`026a01a`](codebook:codebook.version)
+Rendered by CodeBook [`026a01a`](codebook:codebook.version)
```

