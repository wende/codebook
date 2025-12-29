"""Configuration file support for CodeBook.

Supports loading configuration from codebook.yml files.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml


def get_port_from_url(url: str) -> int:
    """Extract port from URL, with sensible defaults."""
    parsed = urlparse(url)
    if parsed.port:
        return parsed.port
    return 443 if parsed.scheme == "https" else 80


@dataclass
class CicadaConfig:
    """Cicada server configuration."""

    enabled: bool = False
    url: str = "http://localhost:9999"
    start: bool = False  # Whether to start cicada server


@dataclass
class BackendConfig:
    """Backend server configuration."""

    url: str = "http://localhost:3000"
    start: bool = False  # Whether to start mock server


DEFAULT_TASK_PREFIX = """\
This file is a diff of a feature specification. I want you to change the code to match the new spec.

"""

DEFAULT_TASK_SUFFIX = """\
---
After completing the task, please update the task file with:
- Description of the feature task that was requested
- Short description of the changes that were made and why
Include implemenentation details how the task was implemented.
Do not include code snippets. Only describe the functional changes that were made.
Do not remove diff lines from the task file.
--- FEATURE TASK ---
...
--- NOTES ---
...
--- SOLUTION ---
"""

DEFAULT_REVIEW_PROMPT = """\
You are a helpful assistant that reviews the task and provides feedback.
You are given a task file that contains a diff of the changes that were made to the codebase.
You need to read the original feature documents that were changed, as well as the diff, and provide feedback on the changes that were made to the codebase. Make sure the documentation describes accurately the changes' functionality.
Append your feedback to the task file starting with the --- REVIEW YYYYMMDDHHMM --- on top. Do not change any other parts of the task file.


This is the task file: [TASK_FILE]
"""


@dataclass
class AIConfig:
    """AI helpers configuration."""

    review_prompt: str = field(default_factory=lambda: DEFAULT_REVIEW_PROMPT)


@dataclass
class CodeBookConfig:
    """CodeBook configuration."""

    # Main directory to watch
    main_dir: str = "codebook"

    # Tasks directory (automatically ignored in watch and render commands)
    # Relative to main_dir. Defaults to {main_dir}/tasks if not specified
    tasks_dir: str = ""

    def __post_init__(self) -> None:
        """Set default tasks_dir based on main_dir if not specified."""
        if not self.tasks_dir:
            self.tasks_dir = str(Path(self.main_dir) / "tasks")

    # Features
    exec: bool = False
    recursive: bool = True

    # Servers
    backend: BackendConfig = field(default_factory=BackendConfig)
    cicada: CicadaConfig = field(default_factory=CicadaConfig)

    # AI helpers
    ai: AIConfig = field(default_factory=AIConfig)

    # Timeouts
    timeout: float = 10.0
    cache_ttl: float = 60.0

    # Task customization
    task_prefix: str = field(default_factory=lambda: DEFAULT_TASK_PREFIX)
    task_suffix: str = field(default_factory=lambda: DEFAULT_TASK_SUFFIX)

    @classmethod
    def load(cls, path: Path | None = None) -> "CodeBookConfig":
        """Load configuration from a YAML file.

        Args:
            path: Path to config file. If None, searches for codebook.yml
                  in current directory and parent directories.

        Returns:
            Loaded configuration, or defaults if no config file found.
        """
        if path is None:
            path = cls._find_config_file()

        if path is None or not path.exists():
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        return cls._from_dict(data)

    @classmethod
    def _find_config_file(cls) -> Path | None:
        """Search for codebook.yml in current and parent directories."""
        current = Path.cwd()

        for _ in range(10):  # Max 10 levels up
            config_path = current / "codebook.yml"
            if config_path.exists():
                return config_path

            config_path = current / "codebook.yaml"
            if config_path.exists():
                return config_path

            parent = current.parent
            if parent == current:
                break
            current = parent

        return None

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "CodeBookConfig":
        """Create config from dictionary."""
        backend_data = data.get("backend", {})
        cicada_data = data.get("cicada", {})

        backend = BackendConfig(
            url=backend_data.get("url", "http://localhost:3000"),
            start=backend_data.get("start", False),
        )

        cicada = CicadaConfig(
            enabled=cicada_data.get("enabled", False),
            url=cicada_data.get("url", "http://localhost:9999"),
            start=cicada_data.get("start", False),
        )

        ai_data = data.get("ai", {})
        ai = AIConfig(
            review_prompt=ai_data.get("review_prompt", DEFAULT_REVIEW_PROMPT),
        )

        main_dir = data.get("main_dir", data.get("watch_dir", "codebook"))
        # Default tasks_dir to {main_dir}/tasks if not specified
        tasks_dir = data.get("tasks_dir", str(Path(main_dir) / "tasks"))

        return cls(
            main_dir=main_dir,
            tasks_dir=tasks_dir,
            exec=data.get("exec", False),
            recursive=data.get("recursive", True),
            backend=backend,
            cicada=cicada,
            ai=ai,
            timeout=data.get("timeout", 10.0),
            cache_ttl=data.get("cache_ttl", 60.0),
            task_prefix=data.get("task-prefix", DEFAULT_TASK_PREFIX),
            task_suffix=data.get("task-suffix", DEFAULT_TASK_SUFFIX),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        result = {
            "main_dir": self.main_dir,
            "tasks_dir": self.tasks_dir,
            "exec": self.exec,
            "recursive": self.recursive,
            "timeout": self.timeout,
            "cache_ttl": self.cache_ttl,
            "backend": {"url": self.backend.url},
            "cicada": {
                "enabled": self.cicada.enabled,
                "url": self.cicada.url,
                "start": self.cicada.start,
            },
        }
        # Only include start if enabled (no backend is bundled by default)
        if self.backend.start:
            result["backend"]["start"] = True
        # Only include AI customization if non-default
        if self.ai.review_prompt != DEFAULT_REVIEW_PROMPT:
            result["ai"] = {"review_prompt": self.ai.review_prompt}
        # Only include task customization if non-default
        if self.task_prefix != DEFAULT_TASK_PREFIX:
            result["task-prefix"] = self.task_prefix
        if self.task_suffix != DEFAULT_TASK_SUFFIX:
            result["task-suffix"] = self.task_suffix
        return result
