This file is a diff of a feature specification. I want you to change the code to match the new spec.

# Error stripping

```diff
diff --git a/.codebook/CODE_EXECUTION.md b/.codebook/CODE_EXECUTION.md
index 14e60b7..375ba1d 100644
--- a/.codebook/CODE_EXECUTION.md
+++ b/.codebook/CODE_EXECUTION.md
@@ -54,7 +54,7 @@ now = datetime.now()
 print(f"Generated: {now.strftime('%Y-%m-%d %H:%M')}")
 </exec>
 <output>
-Generated: 2025-12-27 22:07
+Generated: 2025-12-27 23:00
 </output>
 
 ## State Persistence
@@ -106,7 +106,7 @@ pip install ipykernel
 
 ## Error Handling
 
-Errors are captured and displayed in the output:
+Errors are captured and displayed in the output, stripped of ANSI escape codes:
 
 ```html
 <exec lang="python">
@@ -115,7 +115,7 @@ x = 1 / 0
 <output>
 Error: [31m---------------------------------------------------------------------------[39m
 [31mZeroDivisionError[39m                         Traceback (most recent call last)
-[36mCell[39m[36m [39m[32mIn[7][39m[32m, line 1[39m
+[36mCell[39m[36m [39m[32mIn[14][39m[32m, line 1[39m
 [32m----> [39m[32m1[39m x = [32;43m1[39;49m[43m [49m[43m/[49m[43m [49m[32;43m0[39;49m
 
 [31mZeroDivisionError[39m: division by zero
@@ -124,4 +124,4 @@ Error: [31m--------------------------------------------------------------------
 
 ---
 
-Rendered by CodeBook [`6742eaf`](codebook:codebook.version)
+Rendered by CodeBook [`6742eaf`](codebook:codebook.version)
```

