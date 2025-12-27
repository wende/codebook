"""Tests for the CodeBook CLI interface."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from codebook.cli import main


class TestCLI:
    """Tests for CLI commands."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def temp_dir_in_runner(self, runner: CliRunner):
        """Create a temporary directory within the CLI runner context."""
        with runner.isolated_filesystem() as tmpdir:
            yield Path(tmpdir)

    def test_main_help(self, runner: CliRunner):
        """Should show help message."""
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "CodeBook" in result.output
        assert "render" in result.output
        assert "watch" in result.output
        assert "diff" in result.output

    def test_render_help(self, runner: CliRunner):
        """Should show render command help."""
        result = runner.invoke(main, ["render", "--help"])

        assert result.exit_code == 0
        assert "Render all markdown files" in result.output

    def test_watch_help(self, runner: CliRunner):
        """Should show watch command help."""
        result = runner.invoke(main, ["watch", "--help"])

        assert result.exit_code == 0
        assert "Watch directory" in result.output

    def test_diff_help(self, runner: CliRunner):
        """Should show diff command help."""
        result = runner.invoke(main, ["diff", "--help"])

        assert result.exit_code == 0
        assert "Generate git diff" in result.output

    def test_render_requires_directory(self, runner: CliRunner):
        """Should require directory argument."""
        result = runner.invoke(main, ["render"])

        assert result.exit_code != 0

    def test_render_with_directory(self, runner: CliRunner):
        """Should render files in directory."""
        with runner.isolated_filesystem() as tmpdir:
            # Create test directory and file
            test_dir = Path(tmpdir) / "codebook"
            test_dir.mkdir()
            (test_dir / "test.md").write_text("No links here")

            with patch("codebook.cli.CodeBookClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.resolve_batch.return_value = {}
                mock_client_class.return_value = mock_client

                result = runner.invoke(main, ["render", str(test_dir)])

                assert result.exit_code == 0
                assert "Processed" in result.output

    def test_render_dry_run(self, runner: CliRunner):
        """Should show dry run message."""
        with runner.isolated_filesystem() as tmpdir:
            test_dir = Path(tmpdir) / "codebook"
            test_dir.mkdir()
            (test_dir / "test.md").write_text("[`old`](codebook:test)")

            with patch("codebook.cli.CodeBookClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.resolve_batch.return_value = {"test": "new"}
                mock_client_class.return_value = mock_client

                result = runner.invoke(main, ["render", "--dry-run", str(test_dir)])

                assert result.exit_code == 0
                assert "dry run" in result.output.lower()

    def test_render_reports_statistics(self, runner: CliRunner):
        """Should report rendering statistics."""
        with runner.isolated_filesystem() as tmpdir:
            test_dir = Path(tmpdir) / "codebook"
            test_dir.mkdir()
            (test_dir / "test.md").write_text("[`old`](codebook:test)")

            with patch("codebook.cli.CodeBookClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.resolve_batch.return_value = {"test": "new"}
                mock_client_class.return_value = mock_client

                result = runner.invoke(main, ["render", str(test_dir)])

                assert "Templates found" in result.output
                assert "Templates resolved" in result.output
                assert "Files changed" in result.output

    def test_render_non_recursive(self, runner: CliRunner):
        """Should respect --no-recursive flag."""
        with runner.isolated_filesystem() as tmpdir:
            test_dir = Path(tmpdir) / "codebook"
            test_dir.mkdir()
            subdir = test_dir / "sub"
            subdir.mkdir()
            (test_dir / "root.md").write_text("content")
            (subdir / "nested.md").write_text("content")

            with patch("codebook.cli.CodeBookClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.resolve_batch.return_value = {}
                mock_client_class.return_value = mock_client

                result = runner.invoke(
                    main,
                    ["render", "--no-recursive", str(test_dir)],
                )

                assert result.exit_code == 0
                assert "Processed 1 file" in result.output

    def test_diff_file(self, runner: CliRunner):
        """Should generate diff for file."""
        with runner.isolated_filesystem() as tmpdir:
            # Initialize git repo
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmpdir,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=tmpdir,
                capture_output=True,
            )

            # Create and commit file
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text("[`old`](codebook:test)")
            subprocess.run(["git", "add", "test.md"], cwd=tmpdir, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial"],
                cwd=tmpdir,
                capture_output=True,
            )

            with patch("codebook.cli.CodeBookClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.resolve_batch.return_value = {}
                mock_client_class.return_value = mock_client

                result = runner.invoke(main, ["diff", str(md_file)])

                # Should succeed (may or may not have changes)
                assert result.exit_code == 0

    def test_show_command(self, runner: CliRunner):
        """Should show rendered content."""
        with runner.isolated_filesystem() as tmpdir:
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text("[`old`](codebook:test)")

            with patch("codebook.cli.CodeBookClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.resolve_batch.return_value = {"test": "new"}
                mock_client_class.return_value = mock_client

                result = runner.invoke(main, ["show", str(md_file)])

                assert result.exit_code == 0
                assert "[`new`](codebook:test)" in result.output

    def test_show_requires_file(self, runner: CliRunner):
        """Should error when given directory."""
        with runner.isolated_filesystem() as tmpdir:
            test_dir = Path(tmpdir) / "dir"
            test_dir.mkdir()

            with patch("codebook.cli.CodeBookClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client

                result = runner.invoke(main, ["show", str(test_dir)])

                assert result.exit_code != 0
                assert "Not a file" in result.output

    def test_health_check_success(self, runner: CliRunner):
        """Should report healthy backend."""
        with patch("codebook.cli.CodeBookClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.health_check.return_value = True
            mock_client_class.return_value = mock_client

            result = runner.invoke(main, ["health"])

            assert result.exit_code == 0
            assert "healthy" in result.output.lower()

    def test_health_check_failure(self, runner: CliRunner):
        """Should report unhealthy backend."""
        with patch("codebook.cli.CodeBookClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.health_check.return_value = False
            mock_client_class.return_value = mock_client

            result = runner.invoke(main, ["health"])

            assert result.exit_code != 0
            assert "not responding" in result.output.lower()

    def test_base_url_option(self, runner: CliRunner):
        """Should accept --base-url option."""
        with runner.isolated_filesystem() as tmpdir:
            test_dir = Path(tmpdir) / "codebook"
            test_dir.mkdir()
            (test_dir / "test.md").write_text("content")

            with patch("codebook.cli.CodeBookClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.resolve_batch.return_value = {}
                mock_client_class.return_value = mock_client

                result = runner.invoke(
                    main,
                    ["--base-url", "http://custom:8000", "render", str(test_dir)],
                )

                assert result.exit_code == 0
                mock_client_class.assert_called_once()
                call_kwargs = mock_client_class.call_args
                assert "http://custom:8000" in str(call_kwargs)

    def test_verbose_flag(self, runner: CliRunner):
        """Should enable verbose output."""
        with runner.isolated_filesystem() as tmpdir:
            test_dir = Path(tmpdir) / "codebook"
            test_dir.mkdir()
            (test_dir / "test.md").write_text("content")

            with patch("codebook.cli.CodeBookClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.resolve_batch.return_value = {}
                mock_client_class.return_value = mock_client

                result = runner.invoke(
                    main,
                    ["--verbose", "render", str(test_dir)],
                )

                assert result.exit_code == 0

    def test_timeout_option(self, runner: CliRunner):
        """Should accept --timeout option."""
        with runner.isolated_filesystem() as tmpdir:
            test_dir = Path(tmpdir) / "codebook"
            test_dir.mkdir()
            (test_dir / "test.md").write_text("content")

            with patch("codebook.cli.CodeBookClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.resolve_batch.return_value = {}
                mock_client_class.return_value = mock_client

                result = runner.invoke(
                    main,
                    ["--timeout", "30", "render", str(test_dir)],
                )

                assert result.exit_code == 0

    def test_cache_ttl_option(self, runner: CliRunner):
        """Should accept --cache-ttl option."""
        with runner.isolated_filesystem() as tmpdir:
            test_dir = Path(tmpdir) / "codebook"
            test_dir.mkdir()
            (test_dir / "test.md").write_text("content")

            with patch("codebook.cli.CodeBookClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.resolve_batch.return_value = {}
                mock_client_class.return_value = mock_client

                result = runner.invoke(
                    main,
                    ["--cache-ttl", "120", "render", str(test_dir)],
                )

                assert result.exit_code == 0

    def test_version_option(self, runner: CliRunner):
        """Should show version."""
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "0.1.0" in result.output
