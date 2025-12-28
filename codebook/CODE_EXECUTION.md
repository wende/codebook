# Code Execution

CodeBook can execute Python code blocks and capture their output using Jupyter kernels.
Code Blocks have your project in scope so you can use your own modules and functions.

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
Generated: 2025-12-28 14:15
</output>

## Example: Importing Project Modules

Code blocks have access to your project's modules via `sys.path`:

<exec lang="python">
from codebook.parser import CodeBookParser

content = "[`old`](codebook:my.template)"
parser = CodeBookParser()
links = list(parser.find_links(content))
print(f"Found {len(links)} link(s)")
print(f"Template: {links[0].template}")
</exec>
<output>
Found 1 link(s)
Template: my.template
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

<cicada endpoint="search-module" module_name=".codebook/CODE_EXECUTION.md" format="json" jq="">
{
  "module": ".codebook/CODE_EXECUTION.md",
  "location": ".codebook/CODE_EXECUTION.md:1",
  "moduledoc": null,
  "counts": {
    "public": 0,
    "private": 0
  },
  "functions": []
}
</cicada>

## Error Handling

Errors are captured and displayed in the output, stripped of ANSI escape codes:

```html
<exec lang="python">
x = 1 / 0
</exec>
<output>
Error: ---------------------------------------------------------------------------
ZeroDivisionError                         Traceback (most recent call last)
Cell In[9], line 1
----> 1 x = 1 / 0

ZeroDivisionError: division by zero
</output>
```



---

Rendered by CodeBook [`026a01a`](codebook:codebook.version)

--- BACKLINKS ---
[Code Execution](README.md "codebook:backlink")
