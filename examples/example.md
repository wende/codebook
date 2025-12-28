# CodeBook Example Document

This is an example markdown file with codebook links that demonstrate the system.

## Project Statistics

CICADA supports [`13`](codebook:SCIP.language_count) programming languages.
CICADA supports [`13`](codebook:SCIP.language_count) 

Our project has:
- [`1000`](codebook:metrics.files_indexed) files indexed
- [`5`](codebook:metrics.concurrent_workers) concurrent workers
- Version [`1.2.3`](codebook:project.version)

## API Performance

The API has [`127`](codebook:API.endpoint_count) endpoints.
Average GET response time: [`145ms`](codebook:API.get_response_time)
Test [`145ms`](codebook:API.get_response_time) 

## Build Status

Current CI status: [`Passing`](codebook:CI.build_status)

## Regular Links

This [regular link](https://example.com) is not affected by CodeBook.

## New Format Examples

### Span (inline HTML)
The project is called <span data-codebook="project.name">CICADA</span>.

### URL Link (clickable with dynamic URL)
[View Documentation](https://docs.cicada.dev/api "codebook:API.docs_url")

### Div (multiline content)
<div data-codebook="examples.config">
server:
  port: 3000
  host: localhost
</div>

### Code Execution (Python)
<exec lang="python">

import math
result = math.sqrt(143)
print(f"The square root of 143 is {result}")


</exec>
<output>
The square root of 143 is 11.958260743101398
</output>

### Cicada Code Exploration

Full JSON response:
<cicada endpoint="search-function" format="markdown" function_name="render">
Functions matching render

Found 2 match(es):

---

_file_src.codebook.cli.render()
src/codebook/cli.py:132
*No call sites found*


---

CodeBookLink.render()
src/codebook/parser.py:94
*No call sites found*

</cicada>

Extracted total_matches with jq:
<cicada endpoint="search-function" function_name="render" jq=".total_matches">
2
</cicada>

Extracted first result's module with jq:
<cicada endpoint="search-function" function_name="render" jq=".results[0].module">
_file_src.codebook.cli
</cicada>

Extracted all function signatures with jq:
<cicada endpoint="search-function" function_name="render" jq=".results[*].signature">

</cicada>

## Usage

To render this file:
```bash
codebook render examples/ --base-url http://localhost:3000
```

To watch for changes:
```bash
codebook watch examples/ --base-url http://localhost:3000
```

---

Rendered by CodeBook [`026a01a`](codebook:codebook.version)
