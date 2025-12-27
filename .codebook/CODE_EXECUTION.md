# Code Execution

CodeBook can execute Python code blocks and capture their output using Jupyter kernels.

## Syntax

```html
<exec lang="python">
# Your Python code here
print("Hello, World!")
</exec>
<output>
Hello, World!
</output>
```

## How It Works

1. CodeBook starts a Jupyter kernel when `--exec` is enabled
2. Code blocks are executed in order (state persists between blocks)
3. Output (stdout) replaces the `<output>` section
4. Errors are captured and displayed in the output

## Example: Math Calculation

<exec lang="python">
import math
result = math.pi * 2
print(f"2π = {result:.6f}")
</exec>
<output>
2π = 6.283185
</output>

## Example: Data Processing

<exec lang="python">
data = [1, 2, 3, 4, 5]
total = sum(data)
avg = total / len(data)
print(f"Sum: {total}")
print(f"Average: {avg}")
</exec>
<output>
Sum: 15
Average: 3.0
</output>

## Example: Date/Time

<exec lang="python">
from datetime import datetime
now = datetime.now()
print(f"Generated: {now.strftime('%Y-%m-%d %H:%M')}")
</exec>
<output>
Generated: 2025-12-27 21:13
</output>

## State Persistence

Variables defined in one block are available in subsequent blocks:

<exec lang="python">
# Define a variable
multiplier = 10
</exec>
<output>

</output>

<exec lang="python">
# Use it in another block
result = 5 * multiplier
print(f"5 × {multiplier} = {result}")
</exec>
<output>
5 × 10 = 50
</output>

## Enabling Execution

### Via CLI
```bash
codebook render docs/ --exec
codebook watch docs/ --exec
```

### Via codebook.yml
```yaml
exec: true
```

### Via `codebook run`
```bash
codebook run  # Uses exec setting from codebook.yml
```

## Supported Languages

Currently only Python is supported via `ipykernel`. The kernel must be installed:

```bash
pip install ipykernel
```

## Error Handling

Errors are captured and displayed in the output:

```html
<exec lang="python">
x = 1 / 0
</exec>
<output>
Error: [31m---------------------------------------------------------------------------[39m
[31mZeroDivisionError[39m                         Traceback (most recent call last)
[36mCell[39m[36m [39m[32mIn[7][39m[32m, line 1[39m
[32m----> [39m[32m1[39m x = [32;43m1[39;49m[43m [49m[43m/[49m[43m [49m[32;43m0[39;49m

[31mZeroDivisionError[39m: division by zero
</output>
```

---

Rendered by CodeBook [`dev`](codebook:codebook.version)
