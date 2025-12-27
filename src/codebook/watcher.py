"""File watcher for CodeBook auto-regeneration.

This module monitors markdown files for changes and automatically
re-renders them when modifications are detected. Features:
- Thread-safe debouncing to prevent excessive re-renders
- Configurable debounce delay
- Support for recursive directory watching
"""

import logging
import threading
import time
from pathlib import Path
from typing import Callable

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

from .renderer import CodeBookRenderer

logger = logging.getLogger(__name__)


class DebouncedHandler(FileSystemEventHandler):
    """File system event handler with thread-safe debouncing.

    Waits for a configurable delay after the last modification
    before triggering the callback. This prevents rapid file
    changes from causing excessive re-renders.
    """

    def __init__(
        self,
        callback: Callable[[Path], None],
        debounce_delay: float = 0.5,
    ):
        """Initialize the handler.

        Args:
            callback: Function to call with the file path when triggered
            debounce_delay: Seconds to wait after last modification
        """
        super().__init__()
        self.callback = callback
        self.debounce_delay = debounce_delay
        self._pending: dict[str, float] = {}
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None

    def on_modified(self, event: FileModifiedEvent) -> None:
        """Handle file modification events."""
        if event.is_directory:
            return

        path = Path(event.src_path)
        if path.suffix.lower() != ".md":
            return

        self._schedule_callback(path)

    def on_created(self, event: FileCreatedEvent) -> None:
        """Handle file creation events."""
        if event.is_directory:
            return

        path = Path(event.src_path)
        if path.suffix.lower() != ".md":
            return

        self._schedule_callback(path)

    def _schedule_callback(self, path: Path) -> None:
        """Schedule a debounced callback for a file."""
        with self._lock:
            self._pending[str(path)] = time.time()

            if self._timer is not None:
                self._timer.cancel()

            self._timer = threading.Timer(
                self.debounce_delay,
                self._process_pending,
            )
            self._timer.start()

    def _process_pending(self) -> None:
        """Process all pending file modifications."""
        with self._lock:
            now = time.time()
            threshold = now - self.debounce_delay

            # Find files that haven't been modified recently
            ready = [path for path, timestamp in self._pending.items() if timestamp <= threshold]

            for path_str in ready:
                del self._pending[path_str]
                try:
                    self.callback(Path(path_str))
                except Exception as e:
                    logger.error(f"Error processing {path_str}: {e}")

            # If there are still pending files, reschedule
            if self._pending:
                self._timer = threading.Timer(
                    self.debounce_delay,
                    self._process_pending,
                )
                self._timer.start()
            else:
                self._timer = None


class CodeBookWatcher:
    """File system watcher for CodeBook directories.

    Monitors markdown files for changes and automatically re-renders
    them using the configured renderer.

    Example:
        >>> client = CodeBookClient(base_url="http://localhost:3000")
        >>> renderer = CodeBookRenderer(client)
        >>> watcher = CodeBookWatcher(renderer)
        >>> watcher.watch(Path(".codebook/"))
        >>> watcher.start()  # Blocks until Ctrl+C
    """

    def __init__(
        self,
        renderer: CodeBookRenderer,
        debounce_delay: float = 0.5,
        on_render: Callable[[Path], None] | None = None,
    ):
        """Initialize the watcher.

        Args:
            renderer: Renderer to use for processing files
            debounce_delay: Seconds to wait after last modification
            on_render: Optional callback after file is rendered
        """
        self.renderer = renderer
        self.debounce_delay = debounce_delay
        self.on_render = on_render
        self._observer: Observer | None = None
        self._watching_paths: set[Path] = set()
        self._recently_rendered: dict[str, float] = {}  # Track recently rendered files
        self._render_cooldown = 2.0  # Seconds to ignore events after rendering

    def _handle_file_change(self, path: Path) -> None:
        """Handle a file change event."""
        path_str = str(path.resolve())

        # Skip if this file was recently rendered (prevents infinite loop)
        now = time.time()
        if path_str in self._recently_rendered:
            if now - self._recently_rendered[path_str] < self._render_cooldown:
                logger.debug(f"Skipping recently rendered file: {path}")
                return
            del self._recently_rendered[path_str]

        logger.info(f"File changed: {path}")

        result = self.renderer.render_file(path)

        if result.error:
            logger.error(f"Render error for {path}: {result.error}")
        elif result.changed:
            # Mark as recently rendered to prevent re-triggering
            self._recently_rendered[path_str] = time.time()
            logger.info(
                f"Rendered {path}: {result.templates_resolved}/{result.templates_found} templates"
            )
        else:
            logger.debug(f"No changes for {path}")

        if self.on_render:
            try:
                self.on_render(path)
            except Exception as e:
                logger.error(f"on_render callback error: {e}")

    def watch(self, directory: Path, recursive: bool = True) -> None:
        """Add a directory to the watch list.

        Args:
            directory: Directory to monitor
            recursive: If True, watch subdirectories too
        """
        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        directory = directory.resolve()

        if directory in self._watching_paths:
            logger.warning(f"Already watching: {directory}")
            return

        self._watching_paths.add(directory)

        if self._observer is None:
            self._observer = Observer()

        handler = DebouncedHandler(
            callback=self._handle_file_change,
            debounce_delay=self.debounce_delay,
        )

        self._observer.schedule(handler, str(directory), recursive=recursive)
        logger.info(f"Watching directory: {directory}")

    def start(self) -> None:
        """Start the file watcher.

        Blocks until stop() is called or KeyboardInterrupt.
        """
        if self._observer is None:
            raise RuntimeError("No directories configured for watching")

        logger.info("Starting file watcher...")
        self._observer.start()

        try:
            while self._observer.is_alive():
                self._observer.join(timeout=1)
        except KeyboardInterrupt:
            logger.info("Interrupted, stopping watcher...")
            self.stop()

    def start_async(self) -> None:
        """Start the file watcher in the background.

        Returns immediately. Call stop() to shut down.
        """
        if self._observer is None:
            raise RuntimeError("No directories configured for watching")

        logger.info("Starting file watcher (async)...")
        self._observer.start()

    def stop(self) -> None:
        """Stop the file watcher."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            self._watching_paths.clear()
            logger.info("File watcher stopped")

    def is_running(self) -> bool:
        """Check if the watcher is currently running."""
        return self._observer is not None and self._observer.is_alive()

    @property
    def watching(self) -> set[Path]:
        """Get the set of directories being watched."""
        return self._watching_paths.copy()
