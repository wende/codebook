"""Tests for the CodeBook renderer module."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from codebook.client import CodeBookClient
from codebook.renderer import CodeBookRenderer, RenderResult


class TestRenderResult:
    """Tests for RenderResult dataclass."""

    def test_success_returns_true_when_no_error(self):
        """Should return True when error is None."""
        result = RenderResult(path=Path("test.md"))

        assert result.success is True

    def test_success_returns_false_when_error_present(self):
        """Should return False when error is set."""
        result = RenderResult(path=Path("test.md"), error="Some error")

        assert result.success is False


class TestCodeBookRenderer:
    """Tests for CodeBookRenderer class."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create a mock CodeBook client."""
        client = MagicMock(spec=CodeBookClient)
        client.resolve_batch.return_value = {}
        return client

    @pytest.fixture
    def renderer(self, mock_client: MagicMock) -> CodeBookRenderer:
        """Create a renderer with mock client."""
        return CodeBookRenderer(mock_client)

    def test_render_file_finds_templates(
        self,
        renderer: CodeBookRenderer,
        mock_client: MagicMock,
        temp_dir: Path,
    ):
        """Should find templates in file."""
        md_file = temp_dir / "test.md"
        md_file.write_text("[`value`](codebook:test)")
        mock_client.resolve_batch.return_value = {"test": "resolved"}

        result = renderer.render_file(md_file)

        assert result.templates_found == 1
        mock_client.resolve_batch.assert_called_once_with(["test"])

    def test_render_file_updates_values(
        self,
        renderer: CodeBookRenderer,
        mock_client: MagicMock,
        temp_dir: Path,
    ):
        """Should update file with resolved values."""
        md_file = temp_dir / "test.md"
        md_file.write_text("[`old`](codebook:test)")
        mock_client.resolve_batch.return_value = {"test": "new"}

        result = renderer.render_file(md_file)

        assert result.changed is True
        assert result.templates_resolved == 1
        assert md_file.read_text() == "[`new`](codebook:test)"

    def test_render_file_dry_run_does_not_modify(
        self,
        renderer: CodeBookRenderer,
        mock_client: MagicMock,
        temp_dir: Path,
    ):
        """Should not modify file in dry run mode."""
        md_file = temp_dir / "test.md"
        md_file.write_text("[`old`](codebook:test)")
        mock_client.resolve_batch.return_value = {"test": "new"}

        result = renderer.render_file(md_file, dry_run=True)

        assert result.changed is True
        assert md_file.read_text() == "[`old`](codebook:test)"  # Unchanged

    def test_render_file_handles_no_links(
        self,
        renderer: CodeBookRenderer,
        mock_client: MagicMock,
        temp_dir: Path,
    ):
        """Should handle file with no codebook links."""
        md_file = temp_dir / "test.md"
        md_file.write_text("No links here")

        result = renderer.render_file(md_file)

        assert result.templates_found == 0
        assert result.changed is False
        mock_client.resolve_batch.assert_not_called()

    def test_render_file_handles_read_error(
        self,
        renderer: CodeBookRenderer,
        temp_dir: Path,
    ):
        """Should return error when file cannot be read."""
        md_file = temp_dir / "nonexistent.md"

        result = renderer.render_file(md_file)

        assert result.success is False
        assert "Failed to read file" in result.error

    def test_render_file_handles_write_error(
        self,
        renderer: CodeBookRenderer,
        mock_client: MagicMock,
        temp_dir: Path,
    ):
        """Should return error when file cannot be written."""
        md_file = temp_dir / "test.md"
        md_file.write_text("[`old`](codebook:test)")
        mock_client.resolve_batch.return_value = {"test": "new"}

        # Make file read-only
        md_file.chmod(0o444)

        try:
            result = renderer.render_file(md_file)

            assert result.success is False
            assert "Failed to write file" in result.error
        finally:
            md_file.chmod(0o644)  # Restore permissions

    def test_render_file_handles_unresolved_templates(
        self,
        renderer: CodeBookRenderer,
        mock_client: MagicMock,
        temp_dir: Path,
    ):
        """Should preserve original when templates cannot be resolved."""
        md_file = temp_dir / "test.md"
        md_file.write_text("[`old`](codebook:test)")
        mock_client.resolve_batch.return_value = {}  # No values returned

        result = renderer.render_file(md_file)

        assert result.templates_found == 1
        assert result.templates_resolved == 0
        assert result.changed is False
        assert md_file.read_text() == "[`old`](codebook:test)"

    def test_render_file_partial_resolution(
        self,
        renderer: CodeBookRenderer,
        mock_client: MagicMock,
        temp_dir: Path,
    ):
        """Should update only successfully resolved templates."""
        md_file = temp_dir / "test.md"
        md_file.write_text("[`a`](codebook:first) and [`b`](codebook:second)")
        mock_client.resolve_batch.return_value = {"first": "X"}  # Only one resolved

        result = renderer.render_file(md_file)

        assert result.templates_found == 2
        assert result.templates_resolved == 1
        assert result.changed is True
        assert md_file.read_text() == "[`X`](codebook:first) and [`b`](codebook:second)"

    def test_render_directory_processes_all_md_files(
        self,
        renderer: CodeBookRenderer,
        mock_client: MagicMock,
        temp_dir: Path,
    ):
        """Should process all markdown files in directory."""
        (temp_dir / "file1.md").write_text("[`a`](codebook:test)")
        (temp_dir / "file2.md").write_text("[`b`](codebook:test)")
        (temp_dir / "file3.txt").write_text("[`c`](codebook:test)")  # Not .md
        mock_client.resolve_batch.return_value = {"test": "new"}

        results = renderer.render_directory(temp_dir)

        assert len(results) == 2  # Only .md files

    def test_render_directory_recursive(
        self,
        renderer: CodeBookRenderer,
        mock_client: MagicMock,
        temp_dir: Path,
    ):
        """Should process subdirectories recursively."""
        subdir = temp_dir / "sub"
        subdir.mkdir()
        (temp_dir / "root.md").write_text("[`a`](codebook:test)")
        (subdir / "nested.md").write_text("[`b`](codebook:test)")
        mock_client.resolve_batch.return_value = {"test": "new"}

        results = renderer.render_directory(temp_dir, recursive=True)

        assert len(results) == 2

    def test_render_directory_non_recursive(
        self,
        renderer: CodeBookRenderer,
        mock_client: MagicMock,
        temp_dir: Path,
    ):
        """Should not process subdirectories when recursive=False."""
        subdir = temp_dir / "sub"
        subdir.mkdir()
        (temp_dir / "root.md").write_text("[`a`](codebook:test)")
        (subdir / "nested.md").write_text("[`b`](codebook:test)")
        mock_client.resolve_batch.return_value = {"test": "new"}

        results = renderer.render_directory(temp_dir, recursive=False)

        assert len(results) == 1

    def test_render_directory_handles_invalid_path(
        self,
        renderer: CodeBookRenderer,
        temp_dir: Path,
    ):
        """Should return error for non-directory path."""
        md_file = temp_dir / "file.md"
        md_file.write_text("content")

        results = renderer.render_directory(md_file)

        assert len(results) == 1
        assert results[0].success is False
        assert "Not a directory" in results[0].error

    def test_render_content_returns_rendered_content(
        self,
        renderer: CodeBookRenderer,
        mock_client: MagicMock,
    ):
        """Should return rendered content without file I/O."""
        content = "[`old`](codebook:test)"
        mock_client.resolve_batch.return_value = {"test": "new"}

        rendered, values = renderer.render_content(content)

        assert rendered == "[`new`](codebook:test)"
        assert values == {"test": "new"}

    def test_render_content_handles_no_links(
        self,
        renderer: CodeBookRenderer,
        mock_client: MagicMock,
    ):
        """Should return unchanged content when no links present."""
        content = "No links here"

        rendered, values = renderer.render_content(content)

        assert rendered == content
        assert values == {}
        mock_client.resolve_batch.assert_not_called()

    def test_render_content_handles_no_resolved_values(
        self,
        renderer: CodeBookRenderer,
        mock_client: MagicMock,
    ):
        """Should return unchanged content when values cannot be resolved."""
        content = "[`old`](codebook:test)"
        mock_client.resolve_batch.return_value = {}

        rendered, values = renderer.render_content(content)

        assert rendered == content
        assert values == {}

    def test_render_preserves_surrounding_content(
        self,
        renderer: CodeBookRenderer,
        mock_client: MagicMock,
        temp_dir: Path,
    ):
        """Should preserve non-link content when rendering."""
        md_file = temp_dir / "test.md"
        content = """# Header

Some text before [`value`](codebook:test) and after.

## Subheader

More content.
"""
        md_file.write_text(content)
        mock_client.resolve_batch.return_value = {"test": "NEW"}

        renderer.render_file(md_file)

        result = md_file.read_text()
        assert "# Header" in result
        assert "## Subheader" in result
        assert "[`NEW`](codebook:test)" in result
