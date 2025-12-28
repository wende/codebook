"""HTTP client for resolving CodeBook templates.

This module handles communication with the backend service that resolves
template expressions to their current values. Features include:
- TTL-based caching for performance
- Batch resolution with automatic fallback to individual requests
- Health check endpoint support
"""

import sys
import time
from dataclasses import dataclass, field

import requests


@dataclass
class CacheEntry:
    """A cached response with expiration time."""

    value: str
    expires_at: float


@dataclass
class CodeBookClient:
    """HTTP client for resolving template expressions.

    Communicates with a backend service to resolve template expressions
    to their current values. Supports caching for improved performance.

    Attributes:
        base_url: Base URL of the backend service (e.g., "http://localhost:3000")
        timeout: Request timeout in seconds
        cache_ttl: Cache time-to-live in seconds (0 to disable caching)

    Example:
        >>> client = CodeBookClient(base_url="http://localhost:3000")
        >>> value = client.resolve("SCIP.language_count")
        >>> print(value)  # "13"

        >>> values = client.resolve_batch(["SCIP.language_count", "project.version"])
        >>> print(values)  # {"SCIP.language_count": "13", "project.version": "1.2.3"}
    """

    base_url: str
    timeout: float = 10.0
    cache_ttl: float = 60.0
    _cache: dict[str, CacheEntry] = field(default_factory=dict, repr=False)
    _warned_unreachable: bool = field(default=False, repr=False)

    def resolve(self, template: str) -> str | None:
        """Resolve a single template expression.

        Args:
            template: The template expression to resolve (e.g., "SCIP.language_count")

        Returns:
            The resolved value as a string, or None if resolution failed
        """
        # Check cache first
        cached = self._get_cached(template)
        if cached is not None:
            return cached

        try:
            url = f"{self.base_url.rstrip('/')}/resolve/{template}"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            value = str(data.get("value", ""))

            # Cache the result
            if self.cache_ttl > 0:
                self._set_cached(template, value)

            return value

        except requests.RequestException as e:
            self._warn_unreachable(e)
            return None
        except (ValueError, KeyError):
            # JSON parsing error or missing value key
            return None

    def _warn_unreachable(self, error: Exception) -> None:
        """Print a warning about server being unreachable (once per session)."""
        if self._warned_unreachable:
            return
        self._warned_unreachable = True
        print(
            f"Warning: Server unreachable at {self.base_url} - {error}",
            file=sys.stderr,
        )

    def resolve_batch(self, templates: list[str]) -> dict[str, str]:
        """Resolve multiple template expressions efficiently.

        Attempts batch resolution first via POST /resolve/batch, then
        falls back to individual requests if batch endpoint is unavailable.

        Args:
            templates: List of template expressions to resolve

        Returns:
            Dictionary mapping templates to their resolved values.
            Templates that failed to resolve are omitted.
        """
        if not templates:
            return {}

        # Check which templates are already cached
        results: dict[str, str] = {}
        uncached: list[str] = []

        for template in templates:
            cached = self._get_cached(template)
            if cached is not None:
                results[template] = cached
            else:
                uncached.append(template)

        if not uncached:
            return results

        # Try batch endpoint first
        batch_results = self._resolve_batch_endpoint(uncached)

        if batch_results is not None:
            results.update(batch_results)
        else:
            # Fall back to individual requests
            for template in uncached:
                value = self.resolve(template)
                if value is not None:
                    results[template] = value

        return results

    def _resolve_batch_endpoint(self, templates: list[str]) -> dict[str, str] | None:
        """Try to resolve templates using batch endpoint.

        Args:
            templates: List of template expressions to resolve

        Returns:
            Dictionary of results, or None if batch endpoint is not available
        """
        try:
            url = f"{self.base_url.rstrip('/')}/resolve/batch"
            response = requests.post(
                url,
                json={"templates": templates},
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()
            results: dict[str, str] = {}

            for template, value in data.get("values", {}).items():
                str_value = str(value)
                results[template] = str_value

                # Cache the result
                if self.cache_ttl > 0:
                    self._set_cached(template, str_value)

            return results

        except requests.RequestException:
            return None
        except (ValueError, KeyError):
            return None

    def clear_cache(self) -> None:
        """Clear all cached values."""
        self._cache.clear()

    def _get_cached(self, template: str) -> str | None:
        """Get a cached value if it exists and hasn't expired."""
        if self.cache_ttl <= 0:
            return None

        entry = self._cache.get(template)
        if entry is None:
            return None

        if time.time() > entry.expires_at:
            del self._cache[template]
            return None

        return entry.value

    def _set_cached(self, template: str, value: str) -> None:
        """Cache a resolved value."""
        if self.cache_ttl <= 0:
            return

        self._cache[template] = CacheEntry(
            value=value,
            expires_at=time.time() + self.cache_ttl,
        )

    def health_check(self) -> bool:
        """Check if the backend service is available.

        Returns:
            True if the service responds with 200 OK, False otherwise
        """
        try:
            url = f"{self.base_url.rstrip('/')}/health"
            response = requests.get(url, timeout=self.timeout)
            return response.status_code == 200
        except requests.RequestException:
            return False
