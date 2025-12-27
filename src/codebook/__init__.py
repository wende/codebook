"""CodeBook: Dynamic Markdown Documentation with Live Code References.

A markdown documentation system that embeds live code references using
standard markdown link syntax. It maintains a single source of truth
by storing templates in link URLs and dynamically rendering values inline.

Also supports executing Python code blocks via Jupyter kernels.
"""

import warnings
warnings.filterwarnings("ignore", message=".*GIL.*")

__version__ = "0.1.0"

from .parser import CodeBookParser, CodeBookLink, LinkType
from .client import CodeBookClient
from .renderer import CodeBookRenderer, RenderResult
from .watcher import CodeBookWatcher
from .differ import CodeBookDiffer, DiffResult
from .kernel import CodeBookKernel, ExecutionResult
from .cicada import CicadaClient, CicadaResult
from .config import CodeBookConfig

__all__ = [
    "CodeBookParser",
    "CodeBookLink",
    "LinkType",
    "CodeBookClient",
    "CodeBookRenderer",
    "RenderResult",
    "CodeBookWatcher",
    "CodeBookDiffer",
    "DiffResult",
    "CodeBookKernel",
    "ExecutionResult",
    "CicadaClient",
    "CicadaResult",
    "CodeBookConfig",
]
