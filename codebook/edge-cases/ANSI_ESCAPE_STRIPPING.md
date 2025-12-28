# ANSI Escape Code Stripping

## Problem

Jupyter kernels output error tracebacks with ANSI escape codes for colored terminal output:

```
\x1b[0;31mZeroDivisionError\x1b[0m: division by zero
```

When this is written to a markdown file, the escape codes appear as garbled text:

```
[0;31mZeroDivisionError[0m: division by zero
```

## Solution

CodeBook strips ANSI escape codes from error output before writing to files:

```python
import re

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')

def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub('', text)
```

### Before Stripping

```
Error: ---------------------------------------------------------------------------
[0;31mZeroDivisionError[0m                         Traceback (most recent call last)
Cell [0;32mIn[1][0m, line [0;32m1[0m
[0;31m----> 1[0m x = 1 / 0

[0;31mZeroDivisionError[0m: division by zero
```

### After Stripping

```
Error: ---------------------------------------------------------------------------
ZeroDivisionError                         Traceback (most recent call last)
Cell In[1], line 1
----> 1 x = 1 / 0

ZeroDivisionError: division by zero
```

## Implementation

The stripping happens in the kernel module when capturing execution results:

```python
# src/codebook/kernel.py
if msg_type == "error":
    traceback = "\n".join(content.get("traceback", []))
    # Strip ANSI escape codes
    traceback = strip_ansi(traceback)
```

## Pattern Matched

The regex `\x1b\[[0-9;]*m` matches:
- `\x1b` - Escape character
- `\[` - Opening bracket
- `[0-9;]*` - Zero or more digits and semicolons (color/style codes)
- `m` - End of sequence

Common codes:
- `\x1b[0m` - Reset
- `\x1b[31m` - Red text
- `\x1b[0;31m` - Reset + Red
- `\x1b[1;31m` - Bold + Red

## Code Location

- `src/codebook/kernel.py`
- `src/codebook/renderer.py:_execute_code_blocks()`

---

Rendered by CodeBook

--- BACKLINKS ---
[README](README.md "codebook:backlink")
