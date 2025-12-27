"""Cicada API client for code exploration queries.

This module provides integration with the Cicada code intelligence server,
allowing codebook to render live code exploration results in markdown.
"""

import json
import logging
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)


def jsonpath_get(data: Any, path: str) -> Any:
    """Extract a value from JSON data using a simple path expression.

    Supports:
    - `.key` - access object key
    - `[0]` - access array index
    - `[*]` - get all array elements
    - `.key1.key2[0].key3` - chained access

    Args:
        data: The JSON data (dict, list, or primitive)
        path: The path expression (e.g., ".results[0].function")

    Returns:
        The extracted value, or None if path is invalid

    Examples:
        >>> jsonpath_get({"a": {"b": 1}}, ".a.b")
        1
        >>> jsonpath_get({"items": [{"x": 1}, {"x": 2}]}, ".items[*].x")
        [1, 2]
    """
    if not path or path == ".":
        return data

    # Remove leading dot if present
    if path.startswith("."):
        path = path[1:]

    # Parse path into tokens
    tokens = re.findall(r'(\w+)|\[(\d+|\*)\]', path)

    result = data
    for token in tokens:
        key, index = token
        if key:
            # Object key access
            if isinstance(result, dict):
                result = result.get(key)
            elif isinstance(result, list):
                # Apply to all elements
                result = [item.get(key) if isinstance(item, dict) else None for item in result]
            else:
                return None
        elif index:
            # Array index access
            if index == "*":
                # Get all elements
                if isinstance(result, list):
                    continue  # Keep the list as-is for chaining
                return None
            else:
                idx = int(index)
                if isinstance(result, list) and 0 <= idx < len(result):
                    result = result[idx]
                else:
                    return None

        if result is None:
            return None

    return result


def format_json_value(value: Any, indent: int = 2) -> str:
    """Format a JSON value for display in markdown.

    Args:
        value: The value to format
        indent: Indentation level for JSON output

    Returns:
        Formatted string representation
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        # For lists of strings, join with newlines for better markdown display
        if all(isinstance(item, str) for item in value):
            return "\n\n".join(value)
        return json.dumps(value, indent=indent)
    if isinstance(value, dict):
        return json.dumps(value, indent=indent)
    return str(value)


@dataclass
class CicadaResult:
    """Result from a Cicada API call.

    Attributes:
        success: Whether the API call succeeded
        content: The response content (markdown or JSON string)
        error: Error message if the call failed
        raw_data: The raw parsed data if content was JSON
    """

    success: bool
    content: str
    error: str | None = None
    raw_data: Any = None


class CicadaClient:
    """Client for the Cicada code intelligence API.

    Provides methods to query code structure, search functions/modules,
    and explore code relationships.
    """

    def __init__(self, base_url: str = "http://localhost:9999", timeout: float = 30.0):
        """Initialize the Cicada client.

        Args:
            base_url: Base URL of the Cicada server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _post(self, endpoint: str, data: dict[str, Any]) -> CicadaResult:
        """Make a POST request to the Cicada API.

        Args:
            endpoint: API endpoint (e.g., "/api/query")
            data: Request body data

        Returns:
            CicadaResult with response data
        """
        url = urljoin(self.base_url, endpoint)
        # Default to JSON format if not specified (needed for jq extraction)
        if "format" not in data:
            data["format"] = "json"

        try:
            response = requests.post(
                url,
                json=data,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                data = result.get("data", "")
                # Handle both formats: string (markdown) or dict with content (json)
                if isinstance(data, str):
                    content = data
                else:
                    content = data.get("content", "")

                # Try to parse content as JSON if it looks like JSON
                raw_data = None
                if content and (content.startswith("{") or content.startswith("[")):
                    try:
                        raw_data = json.loads(content)
                    except json.JSONDecodeError:
                        pass

                return CicadaResult(
                    success=True,
                    content=content,
                    raw_data=raw_data,
                )
            else:
                return CicadaResult(
                    success=False,
                    content="",
                    error=result.get("error", "Unknown error"),
                )

        except requests.RequestException as e:
            logger.error(f"Cicada API request failed: {e}")
            return CicadaResult(
                success=False,
                content="",
                error=str(e),
            )

    def query(
        self,
        keywords: list[str] | None = None,
        pattern: str | None = None,
        scope: str = "all",
        filter_type: str = "all",
        match_source: str = "all",
        recent: bool = False,
        path_pattern: str | None = None,
        show_snippets: bool = False,
        format: str | None = None,
    ) -> CicadaResult:
        """Query the codebase semantically.

        Args:
            keywords: List of keywords to search for
            pattern: Module pattern (e.g., "MyApp.User.*")
            scope: 'all' | 'public' | 'private'
            filter_type: 'all' | 'modules' | 'functions'
            match_source: 'all' | 'docs' | 'strings'
            recent: If True, only search files from last 14 days
            path_pattern: File path pattern (e.g., "lib/auth/**")
            show_snippets: Include code snippets in results
            format: Response format ('json' or 'markdown')

        Returns:
            CicadaResult with query results
        """
        data: dict[str, Any] = {
            "scope": scope,
            "filter_type": filter_type,
            "match_source": match_source,
            "recent": recent,
            "show_snippets": show_snippets,
        }

        if keywords:
            data["keywords"] = keywords
        if pattern:
            data["pattern"] = pattern
        if path_pattern:
            data["path_pattern"] = path_pattern
        if format:
            data["format"] = format

        return self._post("/api/query", data)

    def search_module(
        self,
        module_name: str | None = None,
        file_path: str | None = None,
        format: str | None = None,
    ) -> CicadaResult:
        """Search for a specific module.

        Args:
            module_name: Name of the module to find
            file_path: File path to search in
            format: Response format ('json' or 'markdown')

        Returns:
            CicadaResult with module information
        """
        data: dict[str, Any] = {}
        if module_name:
            data["module_name"] = module_name
        if file_path:
            data["file_path"] = file_path
        if format:
            data["format"] = format

        return self._post("/api/search-module", data)

    def search_function(
        self,
        function_name: str,
        module_name: str | None = None,
        arity: int | None = None,
        format: str | None = None,
    ) -> CicadaResult:
        """Search for functions by name.

        Args:
            function_name: Name of the function to find
            module_name: Optional module to search within
            arity: Optional function arity
            format: Response format ('json' or 'markdown')

        Returns:
            CicadaResult with function information
        """
        data: dict[str, Any] = {"function_name": function_name}
        if module_name:
            data["module_name"] = module_name
        if arity is not None:
            data["arity"] = arity
        if format:
            data["format"] = format

        return self._post("/api/search-function", data)

    def git_history(
        self,
        file_path: str | None = None,
        module_name: str | None = None,
        limit: int = 10,
        format: str | None = None,
    ) -> CicadaResult:
        """Get git history for a file or module.

        Args:
            file_path: File path to get history for
            module_name: Module name to get history for
            limit: Maximum number of commits to return
            format: Response format ('json' or 'markdown')

        Returns:
            CicadaResult with git history
        """
        data: dict[str, Any] = {"limit": limit}
        if file_path:
            data["file_path"] = file_path
        if module_name:
            data["module_name"] = module_name
        if format:
            data["format"] = format

        return self._post("/api/git-history", data)

    def query_jq(self, jq_expression: str, data: Any = None) -> CicadaResult:
        """Query using jq expressions.

        Args:
            jq_expression: The jq query expression
            data: Optional data to query against

        Returns:
            CicadaResult with query results
        """
        request_data: dict[str, Any] = {"expression": jq_expression}
        if data is not None:
            request_data["data"] = data

        return self._post("/api/query-jq", request_data)

    def health_check(self) -> bool:
        """Check if the Cicada server is healthy.

        Returns:
            True if server is responding, False otherwise
        """
        try:
            response = requests.get(
                urljoin(self.base_url, "/api/health"),
                timeout=5.0,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False


def format_cicada_result(result: CicadaResult, format_type: str = "markdown") -> str:
    """Format a Cicada result for display.

    Args:
        result: The CicadaResult to format
        format_type: Output format ('markdown', 'json', 'summary')

    Returns:
        Formatted string
    """
    if not result.success:
        return f"Error: {result.error}"

    if format_type == "json" and result.raw_data:
        return json.dumps(result.raw_data, indent=2)

    if format_type == "summary" and result.raw_data:
        # Create a brief summary
        data = result.raw_data
        if isinstance(data, dict):
            if "total_matches" in data:
                return f"Found {data['total_matches']} matches"
            if "results" in data:
                return f"Found {len(data['results'])} results"

    return result.content
