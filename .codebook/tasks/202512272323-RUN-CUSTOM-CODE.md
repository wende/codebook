This file is a diff of a feature specification. I want you to change the code to match the new spec.

# Error stripping

```diff
diff --git a/.codebook/CODE_EXECUTION.md b/.codebook/CODE_EXECUTION.md
index 14e60b7..70e619f 100644
--- a/.codebook/CODE_EXECUTION.md
+++ b/.codebook/CODE_EXECUTION.md
@@ -1,6 +1,7 @@
 # Code Execution
 
 CodeBook can execute Python code blocks and capture their output using Jupyter kernels.
+Code Blocks have your project in scope so you can use your own modules and functions.
 
 ## Syntax
 
@@ -54,7 +55,7 @@ now = datetime.now()
 print(f"Generated: {now.strftime('%Y-%m-%d %H:%M')}")
 </exec>
 <output>
-Generated: 2025-12-27 22:07
+Generated: 2025-12-27 23:23
 </output>
 
 ## State Persistence
@@ -106,22 +107,22 @@ pip install ipykernel
 
 ## Error Handling
 
-Errors are captured and displayed in the output:
+Errors are captured and displayed in the output, stripped of ANSI escape codes:
 
 ```html
 <exec lang="python">
 x = 1 / 0
 </exec>
 <output>
-Error: [31m---------------------------------------------------------------------------[39m
-[31mZeroDivisionError[39m                         Traceback (most recent call last)
-[36mCell[39m[36m [39m[32mIn[7][39m[32m, line 1[39m
-[32m----> [39m[32m1[39m x = [32;43m1[39;49m[43m [49m[43m/[49m[43m [49m[32;43m0[39;49m
+Error: ---------------------------------------------------------------------------
+ZeroDivisionError                         Traceback (most recent call last)
+Cell In[14], line 1
+----> 1 x = 1 / 0
 
-[31mZeroDivisionError[39m: division by zero
+ZeroDivisionError: division by zero
 </output>
 ```
 
 ---
 
-Rendered by CodeBook [`cc99d25`](codebook:codebook.version)
+Rendered by CodeBook [`cc99d25`](codebook:codebook.version)
```

