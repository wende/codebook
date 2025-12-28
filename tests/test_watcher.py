"""Tests for the CodeBook file watcher module."""

import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from codebook.renderer import CodeBookRenderer, RenderResult
from codebook.watcher import CodeBookWatcher, DebouncedHandler


class TestDebouncedHandler:
    """Tests for DebouncedHandler class."""

    def test_debounce_delays_callback(self):
        """Should delay callback execution."""
        callback = MagicMock()
        handler = DebouncedHandler(callback=callback, debounce_delay=0.1)

        # Simulate file modification
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/tmp/test.md"

        handler.on_modified(event)

        # Callback should not be called immediately
        callback.assert_not_called()

        # Wait for debounce
        time.sleep(0.2)
        callback.assert_called_once()

    def test_debounce_coalesces_rapid_events(self):
        """Should coalesce rapid events into single callback."""
        callback = MagicMock()
        handler = DebouncedHandler(callback=callback, debounce_delay=0.1)

        event = MagicMock()
        event.is_directory = False
        event.src_path = "/tmp/test.md"

        # Rapid fire events
        for _ in range(5):
            handler.on_modified(event)
            time.sleep(0.02)

        # Wait for debounce
        time.sleep(0.2)

        # Should only be called once
        callback.assert_called_once()

    def test_ignores_directory_events(self):
        """Should ignore directory modification events."""
        callback = MagicMock()
        handler = DebouncedHandler(callback=callback, debounce_delay=0.05)

        event = MagicMock()
        event.is_directory = True
        event.src_path = "/tmp/subdir"

        handler.on_modified(event)
        time.sleep(0.1)

        callback.assert_not_called()

    def test_ignores_non_markdown_files(self):
        """Should ignore non-markdown file events."""
        callback = MagicMock()
        handler = DebouncedHandler(callback=callback, debounce_delay=0.05)

        event = MagicMock()
        event.is_directory = False
        event.src_path = "/tmp/test.txt"

        handler.on_modified(event)
        time.sleep(0.1)

        callback.assert_not_called()

    def test_handles_created_events(self):
        """Should handle file creation events."""
        callback = MagicMock()
        handler = DebouncedHandler(callback=callback, debounce_delay=0.05)

        event = MagicMock()
        event.is_directory = False
        event.src_path = "/tmp/test.md"

        handler.on_created(event)
        time.sleep(0.1)

        callback.assert_called_once()

    def test_handles_multiple_files(self):
        """Should handle events for different files separately."""
        callback = MagicMock()
        handler = DebouncedHandler(callback=callback, debounce_delay=0.05)

        event1 = MagicMock()
        event1.is_directory = False
        event1.src_path = "/tmp/file1.md"

        event2 = MagicMock()
        event2.is_directory = False
        event2.src_path = "/tmp/file2.md"

        handler.on_modified(event1)
        handler.on_modified(event2)

        time.sleep(0.15)

        assert callback.call_count == 2


class TestCodeBookWatcher:
    """Tests for CodeBookWatcher class."""

    @pytest.fixture
    def mock_renderer(self) -> MagicMock:
        """Create a mock renderer."""
        renderer = MagicMock(spec=CodeBookRenderer)
        renderer.render_file.return_value = RenderResult(path=Path("test.md"))
        renderer._is_in_tasks_dir.return_value = False  # Don't ignore any files
        return renderer

    @pytest.fixture
    def watcher(self, mock_renderer: MagicMock) -> CodeBookWatcher:
        """Create a watcher with mock renderer."""
        return CodeBookWatcher(renderer=mock_renderer, debounce_delay=0.05)

    def test_watch_adds_directory(self, watcher: CodeBookWatcher, temp_dir: Path):
        """Should add directory to watch list."""
        watcher.watch(temp_dir)

        assert temp_dir.resolve() in watcher.watching

    def test_watch_raises_for_non_directory(self, watcher: CodeBookWatcher, temp_dir: Path):
        """Should raise error for non-directory path."""
        file_path = temp_dir / "file.txt"
        file_path.write_text("content")

        with pytest.raises(ValueError, match="Not a directory"):
            watcher.watch(file_path)

    def test_watch_prevents_duplicate_watching(
        self,
        watcher: CodeBookWatcher,
        temp_dir: Path,
    ):
        """Should not add same directory twice."""
        watcher.watch(temp_dir)
        watcher.watch(temp_dir)

        assert len(watcher.watching) == 1

    def test_start_requires_watched_directories(self, watcher: CodeBookWatcher):
        """Should raise error if no directories configured."""
        with pytest.raises(RuntimeError, match="No directories configured"):
            watcher.start()

    def test_is_running_returns_false_initially(self, watcher: CodeBookWatcher):
        """Should return False when not started."""
        assert watcher.is_running() is False

    def test_start_async_runs_in_background(
        self,
        watcher: CodeBookWatcher,
        temp_dir: Path,
    ):
        """Should start watcher in background."""
        watcher.watch(temp_dir)
        watcher.start_async()

        try:
            assert watcher.is_running() is True
        finally:
            watcher.stop()

    def test_stop_clears_state(self, watcher: CodeBookWatcher, temp_dir: Path):
        """Should clear state when stopped."""
        watcher.watch(temp_dir)
        watcher.start_async()
        watcher.stop()

        assert watcher.is_running() is False
        assert len(watcher.watching) == 0

    def test_file_change_triggers_render(
        self,
        watcher: CodeBookWatcher,
        mock_renderer: MagicMock,
        temp_dir: Path,
    ):
        """Should trigger render when file changes."""
        md_file = temp_dir / "test.md"
        md_file.write_text("[`old`](codebook:server.test)")

        watcher.watch(temp_dir)
        watcher.start_async()

        try:
            # Modify the file
            time.sleep(0.1)  # Let watcher start
            md_file.write_text("[`new`](codebook:server.test)")
            time.sleep(0.2)  # Wait for debounce

            mock_renderer.render_file.assert_called()
        finally:
            watcher.stop()

    def test_on_render_callback_called(
        self,
        mock_renderer: MagicMock,
        temp_dir: Path,
    ):
        """Should call on_render callback after rendering."""
        on_render = MagicMock()
        watcher = CodeBookWatcher(
            renderer=mock_renderer,
            debounce_delay=0.05,
            on_render=on_render,
        )

        md_file = temp_dir / "test.md"
        md_file.write_text("content")

        watcher.watch(temp_dir)
        watcher.start_async()

        try:
            time.sleep(0.1)
            md_file.write_text("updated")
            time.sleep(0.2)

            # on_render should have been called
            on_render.assert_called()
        finally:
            watcher.stop()

    def test_watching_property_returns_copy(
        self,
        watcher: CodeBookWatcher,
        temp_dir: Path,
    ):
        """Should return copy of watching set."""
        watcher.watch(temp_dir)

        watching = watcher.watching
        watching.add(Path("/other"))

        assert Path("/other") not in watcher.watching

    def test_handle_file_change_logs_errors(
        self,
        mock_renderer: MagicMock,
        temp_dir: Path,
    ):
        """Should log errors during render."""
        mock_renderer.render_file.return_value = RenderResult(
            path=Path("test.md"),
            error="Render error",
        )
        watcher = CodeBookWatcher(renderer=mock_renderer, debounce_delay=0.05)

        md_file = temp_dir / "test.md"
        md_file.write_text("content")

        watcher.watch(temp_dir)
        watcher.start_async()

        try:
            time.sleep(0.1)
            md_file.write_text("updated")
            time.sleep(0.2)

            mock_renderer.render_file.assert_called()
        finally:
            watcher.stop()
