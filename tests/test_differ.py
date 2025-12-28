"""Tests for the CodeBook git diff generator module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from codebook.renderer import CodeBookRenderer
from codebook.differ import CodeBookDiffer, DiffResult


class TestDiffResult:
    """Tests for DiffResult dataclass."""

    def test_success_returns_true_when_no_error(self):
        """Should return True when error is None."""
        result = DiffResult(diff="some diff")

        assert result.success is True

    def test_success_returns_false_when_error_present(self):
        """Should return False when error is set."""
        result = DiffResult(diff="", error="Some error")

        assert result.success is False

    def test_has_changes_returns_true_when_diff_present(self):
        """Should return True when diff has content."""
        result = DiffResult(diff="--- a/file\n+++ b/file")

        assert result.has_changes is True

    def test_has_changes_returns_false_when_diff_empty(self):
        """Should return False when diff is empty."""
        result = DiffResult(diff="")

        assert result.has_changes is False

    def test_has_changes_returns_false_for_whitespace_only(self):
        """Should return False when diff contains only whitespace."""
        result = DiffResult(diff="   \n\n  ")

        assert result.has_changes is False


class TestCodeBookDiffer:
    """Tests for CodeBookDiffer class."""

    @pytest.fixture
    def mock_renderer(self) -> MagicMock:
        """Create a mock renderer."""
        renderer = MagicMock(spec=CodeBookRenderer)
        renderer.render_content.return_value = ("content", {})
        renderer._is_in_tasks_dir.return_value = False  # Don't filter any files by default
        return renderer

    @pytest.fixture
    def differ(self, mock_renderer: MagicMock) -> CodeBookDiffer:
        """Create a differ with mock renderer."""
        return CodeBookDiffer(mock_renderer)

    def test_diff_file_returns_error_for_nonexistent_file(
        self,
        differ: CodeBookDiffer,
        temp_dir: Path,
    ):
        """Should return error for nonexistent file."""
        result = differ.diff_file(temp_dir / "nonexistent.md")

        assert result.success is False
        assert "File not found" in result.error

    def test_diff_file_returns_error_outside_git_repo(
        self,
        differ: CodeBookDiffer,
        temp_dir: Path,
    ):
        """Should return error when not in git repository."""
        md_file = temp_dir / "test.md"
        md_file.write_text("[`value`](codebook:test)")

        result = differ.diff_file(md_file)

        assert result.success is False
        assert "git repository" in result.error.lower()

    def test_diff_file_in_git_repo(
        self,
        mock_renderer: MagicMock,
        git_repo: Path,
    ):
        """Should generate diff in git repository."""
        differ = CodeBookDiffer(mock_renderer)

        # Create and commit a file
        md_file = git_repo / "test.md"
        md_file.write_text("[`old`](codebook:test)")
        subprocess.run(["git", "add", "test.md"], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=git_repo,
            capture_output=True,
        )

        # Modify the file
        md_file.write_text("[`new`](codebook:test)")

        # Mock renderer to return different content
        mock_renderer.render_content.return_value = ("[`new`](codebook:test)", {"test": "new"})

        result = differ.diff_file(md_file)

        assert result.files_processed == 1

    def test_diff_directory_processes_all_md_files(
        self,
        mock_renderer: MagicMock,
        git_repo: Path,
    ):
        """Should process all markdown files in directory."""
        differ = CodeBookDiffer(mock_renderer)

        # Create and commit files
        (git_repo / "file1.md").write_text("content1")
        (git_repo / "file2.md").write_text("content2")
        subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=git_repo,
            capture_output=True,
        )

        result = differ.diff_directory(git_repo)

        assert result.files_processed >= 2

    def test_diff_directory_returns_error_for_non_directory(
        self,
        differ: CodeBookDiffer,
        temp_dir: Path,
    ):
        """Should return error for non-directory path."""
        md_file = temp_dir / "test.md"
        md_file.write_text("content")

        result = differ.diff_directory(md_file)

        assert result.success is False
        assert "Not a directory" in result.error

    def test_diff_directory_recursive(
        self,
        mock_renderer: MagicMock,
        git_repo: Path,
    ):
        """Should process subdirectories recursively."""
        differ = CodeBookDiffer(mock_renderer)

        # Create nested structure
        subdir = git_repo / "sub"
        subdir.mkdir()
        (git_repo / "root.md").write_text("content")
        (subdir / "nested.md").write_text("content")
        subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=git_repo,
            capture_output=True,
        )

        result = differ.diff_directory(git_repo, recursive=True)

        assert result.files_processed >= 2

    def test_diff_directory_non_recursive(
        self,
        mock_renderer: MagicMock,
        git_repo: Path,
    ):
        """Should not process subdirectories when recursive=False."""
        differ = CodeBookDiffer(mock_renderer)

        # Create nested structure
        subdir = git_repo / "sub"
        subdir.mkdir()
        (git_repo / "root.md").write_text("content")
        (subdir / "nested.md").write_text("content")
        subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=git_repo,
            capture_output=True,
        )

        result = differ.diff_directory(git_repo, recursive=False)

        # Should only process root.md
        assert result.files_processed == 1

    def test_show_rendered_returns_rendered_content(
        self,
        mock_renderer: MagicMock,
        temp_dir: Path,
    ):
        """Should return rendered content."""
        differ = CodeBookDiffer(mock_renderer)

        md_file = temp_dir / "test.md"
        md_file.write_text("[`old`](codebook:test)")
        mock_renderer.render_content.return_value = (
            "[`new`](codebook:test)",
            {"test": "new"},
        )

        result = differ.show_rendered(md_file)

        assert result == "[`new`](codebook:test)"

    def test_show_rendered_returns_none_on_error(
        self,
        mock_renderer: MagicMock,
        temp_dir: Path,
    ):
        """Should return None when file cannot be read."""
        differ = CodeBookDiffer(mock_renderer)

        result = differ.show_rendered(temp_dir / "nonexistent.md")

        assert result is None

    def test_get_git_root_finds_root(
        self,
        differ: CodeBookDiffer,
        git_repo: Path,
    ):
        """Should find git repository root."""
        subdir = git_repo / "sub"
        subdir.mkdir()

        root = differ._get_git_root(subdir)

        # Use resolve() to handle symlinks (e.g., macOS /var -> /private/var)
        assert root.resolve() == git_repo.resolve()

    def test_get_git_root_returns_none_outside_repo(
        self,
        differ: CodeBookDiffer,
        temp_dir: Path,
    ):
        """Should return None when not in git repository."""
        root = differ._get_git_root(temp_dir)

        assert root is None

    def test_diff_combines_multiple_files(
        self,
        mock_renderer: MagicMock,
        git_repo: Path,
    ):
        """Should combine diffs from multiple files."""
        differ = CodeBookDiffer(mock_renderer)

        # Create and commit files
        (git_repo / "file1.md").write_text("[`a`](codebook:test)")
        (git_repo / "file2.md").write_text("[`b`](codebook:test)")
        subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=git_repo,
            capture_output=True,
        )

        # Modify files
        (git_repo / "file1.md").write_text("[`A`](codebook:test)")
        (git_repo / "file2.md").write_text("[`B`](codebook:test)")

        # Mock render to return modified content
        def render_side_effect(content):
            return (content, {})

        mock_renderer.render_content.side_effect = render_side_effect

        result = differ.diff_directory(git_repo)

        # Both files should be processed
        assert result.files_processed >= 2
