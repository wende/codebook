"""Tests for the CodeBook HTTP client module."""

import time

import pytest
import responses

from codebook.client import CodeBookClient, CacheEntry


class TestCodeBookClient:
    """Tests for CodeBookClient class."""

    @pytest.fixture
    def base_url(self) -> str:
        return "http://localhost:3000"

    @pytest.fixture
    def client(self, base_url: str) -> CodeBookClient:
        return CodeBookClient(base_url=base_url, cache_ttl=0)

    @pytest.fixture
    def cached_client(self, base_url: str) -> CodeBookClient:
        return CodeBookClient(base_url=base_url, cache_ttl=60.0)

    @responses.activate
    def test_resolve_returns_value_on_success(self, client: CodeBookClient, base_url: str):
        """Should return resolved value when backend responds successfully."""
        responses.add(
            responses.GET,
            f"{base_url}/resolve/test.metric",
            json={"value": 42},
            status=200,
        )

        result = client.resolve("test.metric")

        assert result == "42"

    @responses.activate
    def test_resolve_returns_string_value(self, client: CodeBookClient, base_url: str):
        """Should convert numeric values to strings."""
        responses.add(
            responses.GET,
            f"{base_url}/resolve/test.metric",
            json={"value": 3.14159},
            status=200,
        )

        result = client.resolve("test.metric")

        assert result == "3.14159"

    @responses.activate
    def test_resolve_returns_none_on_http_error(self, client: CodeBookClient, base_url: str):
        """Should return None when backend returns error."""
        responses.add(
            responses.GET,
            f"{base_url}/resolve/test.metric",
            status=500,
        )

        result = client.resolve("test.metric")

        assert result is None

    @responses.activate
    def test_resolve_returns_none_on_invalid_json(self, client: CodeBookClient, base_url: str):
        """Should return None when response is not valid JSON."""
        responses.add(
            responses.GET,
            f"{base_url}/resolve/test.metric",
            body="not json",
            status=200,
        )

        result = client.resolve("test.metric")

        assert result is None

    @responses.activate
    def test_resolve_returns_none_when_value_key_missing(
        self,
        client: CodeBookClient,
        base_url: str,
    ):
        """Should return empty string when value key is missing."""
        responses.add(
            responses.GET,
            f"{base_url}/resolve/test.metric",
            json={"other": "data"},
            status=200,
        )

        result = client.resolve("test.metric")

        assert result == ""

    @responses.activate
    def test_resolve_returns_none_on_network_error(self, client: CodeBookClient):
        """Should return None when network error occurs."""
        responses.add(
            responses.GET,
            "http://localhost:3000/resolve/test.metric",
            body=responses.ConnectionError(),
        )

        result = client.resolve("test.metric")

        assert result is None

    @responses.activate
    def test_resolve_batch_resolves_multiple_templates(
        self,
        client: CodeBookClient,
        base_url: str,
    ):
        """Should resolve multiple templates."""
        responses.add(
            responses.POST,
            f"{base_url}/resolve/batch",
            json={"values": {"a": 1, "b": 2}},
            status=200,
        )

        result = client.resolve_batch(["a", "b"])

        assert result == {"a": "1", "b": "2"}

    @responses.activate
    def test_resolve_batch_falls_back_to_individual_requests(
        self,
        client: CodeBookClient,
        base_url: str,
    ):
        """Should fall back to individual requests if batch fails."""
        responses.add(
            responses.POST,
            f"{base_url}/resolve/batch",
            status=404,
        )
        responses.add(
            responses.GET,
            f"{base_url}/resolve/a",
            json={"value": 1},
            status=200,
        )
        responses.add(
            responses.GET,
            f"{base_url}/resolve/b",
            json={"value": 2},
            status=200,
        )

        result = client.resolve_batch(["a", "b"])

        assert result == {"a": "1", "b": "2"}

    def test_resolve_batch_returns_empty_dict_for_empty_input(
        self,
        client: CodeBookClient,
    ):
        """Should return empty dict when no templates provided."""
        result = client.resolve_batch([])

        assert result == {}

    @responses.activate
    def test_caching_returns_cached_value(self, cached_client: CodeBookClient, base_url: str):
        """Should return cached value on subsequent calls."""
        responses.add(
            responses.GET,
            f"{base_url}/resolve/test.metric",
            json={"value": 42},
            status=200,
        )

        result1 = cached_client.resolve("test.metric")
        result2 = cached_client.resolve("test.metric")

        assert result1 == "42"
        assert result2 == "42"
        assert len(responses.calls) == 1  # Only one HTTP call

    @responses.activate
    def test_caching_respects_ttl(self, base_url: str):
        """Should refetch after cache expires."""
        client = CodeBookClient(base_url=base_url, cache_ttl=0.1)

        responses.add(
            responses.GET,
            f"{base_url}/resolve/test.metric",
            json={"value": 42},
            status=200,
        )
        responses.add(
            responses.GET,
            f"{base_url}/resolve/test.metric",
            json={"value": 99},
            status=200,
        )

        result1 = client.resolve("test.metric")
        time.sleep(0.2)
        result2 = client.resolve("test.metric")

        assert result1 == "42"
        assert result2 == "99"
        assert len(responses.calls) == 2

    @responses.activate
    def test_clear_cache_removes_all_cached_values(
        self,
        cached_client: CodeBookClient,
        base_url: str,
    ):
        """Should clear all cached values."""
        responses.add(
            responses.GET,
            f"{base_url}/resolve/test.metric",
            json={"value": 42},
            status=200,
        )
        responses.add(
            responses.GET,
            f"{base_url}/resolve/test.metric",
            json={"value": 99},
            status=200,
        )

        cached_client.resolve("test.metric")
        cached_client.clear_cache()
        result = cached_client.resolve("test.metric")

        assert result == "99"
        assert len(responses.calls) == 2

    @responses.activate
    def test_resolve_batch_uses_cache(self, cached_client: CodeBookClient, base_url: str):
        """Should use cached values in batch resolution."""
        responses.add(
            responses.GET,
            f"{base_url}/resolve/a",
            json={"value": 1},
            status=200,
        )
        responses.add(
            responses.POST,
            f"{base_url}/resolve/batch",
            json={"values": {"b": 2}},
            status=200,
        )

        # Prime cache with one value
        cached_client.resolve("a")

        # Batch should only fetch uncached value
        result = cached_client.resolve_batch(["a", "b"])

        assert result == {"a": "1", "b": "2"}

    @responses.activate
    def test_health_check_returns_true_on_success(
        self,
        client: CodeBookClient,
        base_url: str,
    ):
        """Should return True when health endpoint responds."""
        responses.add(
            responses.GET,
            f"{base_url}/health",
            status=200,
        )

        result = client.health_check()

        assert result is True

    @responses.activate
    def test_health_check_returns_false_on_error(
        self,
        client: CodeBookClient,
        base_url: str,
    ):
        """Should return False when health endpoint fails."""
        responses.add(
            responses.GET,
            f"{base_url}/health",
            status=500,
        )

        result = client.health_check()

        assert result is False

    @responses.activate
    def test_health_check_returns_false_on_network_error(
        self,
        client: CodeBookClient,
    ):
        """Should return False on network error."""
        responses.add(
            responses.GET,
            "http://localhost:3000/health",
            body=responses.ConnectionError(),
        )

        result = client.health_check()

        assert result is False

    def test_base_url_trailing_slash_handling(self):
        """Should handle base URL with or without trailing slash."""
        client1 = CodeBookClient(base_url="http://localhost:3000")
        client2 = CodeBookClient(base_url="http://localhost:3000/")

        # Both should produce same effective URL
        assert client1.base_url.rstrip("/") == client2.base_url.rstrip("/")

    @responses.activate
    def test_timeout_configuration(self, base_url: str):
        """Should use configured timeout."""
        client = CodeBookClient(base_url=base_url, timeout=5.0)

        responses.add(
            responses.GET,
            f"{base_url}/resolve/test",
            json={"value": 1},
            status=200,
        )

        client.resolve("test")

        assert client.timeout == 5.0


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_cache_entry_stores_value_and_expiration(self):
        """Should store value and expiration time."""
        entry = CacheEntry(value="test", expires_at=1234567890.0)

        assert entry.value == "test"
        assert entry.expires_at == 1234567890.0
