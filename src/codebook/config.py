"""Configuration file support for CodeBook.

Supports loading configuration from codebook.yml files.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class CicadaConfig:
    """Cicada server configuration."""

    enabled: bool = False
    url: str = "http://localhost:9999"
    port: int = 9999
    start: bool = False  # Whether to start cicada server


@dataclass
class BackendConfig:
    """Backend server configuration."""

    url: str = "http://localhost:3000"
    port: int = 3000
    start: bool = False  # Whether to start mock server


DEFAULT_TASK_PREFIX = """\
This file is a diff of a feature specification. I want you to change the code to match the new spec.

"""


@dataclass
class CodeBookConfig:
    """CodeBook configuration."""

    # Watch directory
    watch_dir: str = "."

    # Features
    exec: bool = False
    recursive: bool = True

    # Servers
    backend: BackendConfig = field(default_factory=BackendConfig)
    cicada: CicadaConfig = field(default_factory=CicadaConfig)

    # Timeouts
    timeout: float = 10.0
    cache_ttl: float = 60.0

    # Task customization
    task_prefix: str = field(default_factory=lambda: DEFAULT_TASK_PREFIX)
    task_suffix: str = ""

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

        with open(path, "r") as f:
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
            port=backend_data.get("port", 3000),
            start=backend_data.get("start", False),
        )

        cicada = CicadaConfig(
            enabled=cicada_data.get("enabled", False),
            url=cicada_data.get("url", "http://localhost:9999"),
            port=cicada_data.get("port", 9999),
            start=cicada_data.get("start", False),
        )

        return cls(
            watch_dir=data.get("watch_dir", "."),
            exec=data.get("exec", False),
            recursive=data.get("recursive", True),
            backend=backend,
            cicada=cicada,
            timeout=data.get("timeout", 10.0),
            cache_ttl=data.get("cache_ttl", 60.0),
            task_prefix=data.get("task-prefix", DEFAULT_TASK_PREFIX),
            task_suffix=data.get("task-suffix", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        result = {
            "watch_dir": self.watch_dir,
            "exec": self.exec,
            "recursive": self.recursive,
            "timeout": self.timeout,
            "cache_ttl": self.cache_ttl,
            "backend": {
                "url": self.backend.url,
                "port": self.backend.port,
                "start": self.backend.start,
            },
            "cicada": {
                "enabled": self.cicada.enabled,
                "url": self.cicada.url,
                "port": self.cicada.port,
                "start": self.cicada.start,
            },
        }
        # Only include task customization if non-default
        if self.task_prefix != DEFAULT_TASK_PREFIX:
            result["task-prefix"] = self.task_prefix
        if self.task_suffix:
            result["task-suffix"] = self.task_suffix
        return result
