"""Shared test fixtures and configuration."""

import warnings

# Suppress GIL warning from ujson on Python 3.13+ free-threaded builds
warnings.filterwarnings(
    "ignore",
    message="The global interpreter lock.*",
    category=RuntimeWarning,
)

import subprocess
import tempfile
from pathlib import Path
from typing import Iterator

import pytest
import responses

from codebook.client import CodeBookClient
from codebook.renderer import CodeBookRenderer


@pytest.fixture
def base_url() -> str:
    """Backend service base URL for testing."""
    return "http://localhost:3000"


@pytest.fixture
def client(base_url: str) -> CodeBookClient:
    """CodeBook HTTP client."""
    return CodeBookClient(base_url=base_url, cache_ttl=0)


@pytest.fixture
def client_with_cache(base_url: str) -> CodeBookClient:
    """CodeBook HTTP client with caching enabled."""
    return CodeBookClient(base_url=base_url, cache_ttl=60.0)


@pytest.fixture
def renderer(client: CodeBookClient) -> CodeBookRenderer:
    """CodeBook renderer."""
    return CodeBookRenderer(client)


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Temporary directory for file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_markdown() -> str:
    """Sample markdown content with codebook links."""
    return """# Documentation

CICADA supports [`13`](codebook:SCIP.language_count) languages.

## Features

- Fast indexing with [`1000`](codebook:metrics.files_indexed) files
- Supports [`5`](codebook:metrics.concurrent_workers) concurrent workers

Some regular [link](https://example.com) here.
"""


@pytest.fixture
def sample_markdown_file(temp_dir: Path, sample_markdown: str) -> Path:
    """Create a sample markdown file with codebook links."""
    md_file = temp_dir / "test.md"
    md_file.write_text(sample_markdown, encoding="utf-8")
    return md_file


@pytest.fixture
def mock_responses() -> Iterator[responses.RequestsMock]:
    """Mock HTTP responses."""
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def git_repo(temp_dir: Path) -> Path:
    """Create a temporary git repository."""
    subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=temp_dir,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=temp_dir,
        capture_output=True,
    )

    return temp_dir
