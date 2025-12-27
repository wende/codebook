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


class TestTaskCommands:
    """Tests for task subcommands."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def git_repo(self, runner: CliRunner):
        """Create a temporary git repository with the CLI runner."""
        with runner.isolated_filesystem() as tmpdir:
            tmpdir_path = Path(tmpdir)
            # Initialize git repo
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmpdir,
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=tmpdir,
                capture_output=True,
                check=True,
            )
            yield tmpdir_path

    def test_task_help(self, runner: CliRunner):
        """Should show task group help."""
        result = runner.invoke(main, ["task", "--help"])

        assert result.exit_code == 0
        assert "Manage CodeBook tasks" in result.output
        assert "new" in result.output
        assert "list" in result.output
        assert "delete" in result.output

    def test_task_new_help(self, runner: CliRunner):
        """Should show task new help."""
        result = runner.invoke(main, ["task", "new", "--help"])

        assert result.exit_code == 0
        assert "Create a new task" in result.output
        assert "--all" in result.output

    def test_task_new_with_modified_file(self, git_repo: Path):
        """Should create task with modified file diff."""
        runner = CliRunner()

        # Create and commit a file
        md_file = git_repo / "test.md"
        md_file.write_text("Original content")
        subprocess.run(["git", "add", "test.md"], cwd=git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=git_repo, capture_output=True)

        # Modify the file
        md_file.write_text("Modified content")

        # Create task
        result = runner.invoke(
            main,
            ["task", "new", "Test Task", str(md_file)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "Created task:" in result.output
        assert "1 file(s)" in result.output

        # Verify task file was created
        tasks_dir = git_repo / ".codebook" / "tasks"
        task_files = list(tasks_dir.glob("*.md"))
        assert len(task_files) == 1
        assert "TEST_TASK" in task_files[0].name

        # Verify task content contains diff
        content = task_files[0].read_text()
        assert "```diff" in content
        assert "-Original content" in content
        assert "+Modified content" in content

    def test_task_new_with_untracked_file(self, git_repo: Path):
        """Should create task with untracked (new) file."""
        runner = CliRunner()

        # Create a new file (not tracked by git)
        md_file = git_repo / "new_file.md"
        md_file.write_text("Brand new content\nWith multiple lines")

        # Create task
        result = runner.invoke(
            main,
            ["task", "new", "New File Task", str(md_file)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "Created task:" in result.output
        assert "1 file(s)" in result.output

        # Verify task file was created
        tasks_dir = git_repo / ".codebook" / "tasks"
        task_files = list(tasks_dir.glob("*.md"))
        assert len(task_files) == 1

        # Verify task content shows new file as added
        content = task_files[0].read_text()
        assert "```diff" in content
        assert "new file mode" in content
        assert "+Brand new content" in content
        assert "+With multiple lines" in content

    def test_task_new_with_directory_scope(self, git_repo: Path):
        """Should create task with all modified/untracked files in directory."""
        runner = CliRunner()

        # Create docs directory
        docs_dir = git_repo / "docs"
        docs_dir.mkdir()

        # Create and commit a file
        doc1 = docs_dir / "doc1.md"
        doc1.write_text("Original doc1")
        subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=git_repo, capture_output=True)

        # Modify doc1 and add new doc2
        doc1.write_text("Modified doc1")
        doc2 = docs_dir / "doc2.md"
        doc2.write_text("New doc2")

        # Create task
        result = runner.invoke(
            main,
            ["task", "new", "Docs Update", str(docs_dir)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "2 file(s)" in result.output

        # Verify content includes both files
        tasks_dir = git_repo / ".codebook" / "tasks"
        task_files = list(tasks_dir.glob("*.md"))
        content = task_files[0].read_text()
        assert "Modified doc1" in content
        assert "New doc2" in content

    def test_task_new_no_modified_files(self, git_repo: Path):
        """Should error when no modified files found."""
        runner = CliRunner()

        # Create and commit a file (no modifications after commit)
        md_file = git_repo / "test.md"
        md_file.write_text("Committed content")
        subprocess.run(["git", "add", "test.md"], cwd=git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=git_repo, capture_output=True)

        # Create task (no changes)
        result = runner.invoke(
            main,
            ["task", "new", "Empty Task", str(md_file)],
        )

        assert result.exit_code == 0  # Click returns 0, message to stderr
        assert "No modified markdown files found" in result.output

    def test_task_new_with_all_flag(self, git_repo: Path):
        """Should include all files when --all is specified."""
        runner = CliRunner()

        # Create and commit a file (no modifications)
        md_file = git_repo / "test.md"
        md_file.write_text("Committed content")
        subprocess.run(["git", "add", "test.md"], cwd=git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=git_repo, capture_output=True)

        # Create task with --all (still no diff available for committed unchanged file)
        result = runner.invoke(
            main,
            ["task", "new", "All Files Task", str(md_file), "--all"],
        )

        # File exists but has no diff, so still reports no modified files
        assert "No modified markdown files found" in result.output

    def test_task_new_title_conversion(self, git_repo: Path):
        """Should convert title to UPPER_SNAKE_CASE."""
        runner = CliRunner()

        # Create untracked file
        md_file = git_repo / "test.md"
        md_file.write_text("Content")

        result = runner.invoke(
            main,
            ["task", "new", "My Special Task!", str(md_file)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        tasks_dir = git_repo / ".codebook" / "tasks"
        task_files = list(tasks_dir.glob("*.md"))
        assert len(task_files) == 1
        assert "MY_SPECIAL_TASK" in task_files[0].name

    def test_task_list_empty(self, runner: CliRunner):
        """Should show message when no tasks exist."""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["task", "list"])

            assert result.exit_code == 0
            assert "No tasks" in result.output

    def test_task_list_shows_tasks(self, git_repo: Path):
        """Should list existing tasks with formatted dates."""
        runner = CliRunner()

        # Create tasks directory with task files
        tasks_dir = git_repo / ".codebook" / "tasks"
        tasks_dir.mkdir(parents=True)

        # Create task files with different formats
        (tasks_dir / "202412281530-FIRST_TASK.md").write_text("Task 1")
        (tasks_dir / "202412281545-SECOND_TASK.md").write_text("Task 2")

        result = runner.invoke(main, ["task", "list"])

        assert result.exit_code == 0
        assert "Tasks:" in result.output
        assert "2024-12-28 15:30" in result.output
        assert "FIRST_TASK" in result.output
        assert "2024-12-28 15:45" in result.output
        assert "SECOND_TASK" in result.output

    def test_task_list_handles_old_format(self, git_repo: Path):
        """Should handle old date format (YYYYMMDD-)."""
        runner = CliRunner()

        tasks_dir = git_repo / ".codebook" / "tasks"
        tasks_dir.mkdir(parents=True)
        (tasks_dir / "20241228-OLD_FORMAT_TASK.md").write_text("Old task")

        result = runner.invoke(main, ["task", "list"])

        assert result.exit_code == 0
        assert "2024-12-28" in result.output
        assert "OLD_FORMAT_TASK" in result.output

    def test_task_delete_by_title(self, git_repo: Path):
        """Should delete task by title with --force."""
        runner = CliRunner()

        tasks_dir = git_repo / ".codebook" / "tasks"
        tasks_dir.mkdir(parents=True)
        task_file = tasks_dir / "202412281530-MY_TASK.md"
        task_file.write_text("Task content")

        result = runner.invoke(
            main,
            ["task", "delete", "My Task", "--force"],
        )

        assert result.exit_code == 0
        assert "Deleted:" in result.output
        assert not task_file.exists()

    def test_task_delete_not_found(self, git_repo: Path):
        """Should error when task not found."""
        runner = CliRunner()

        tasks_dir = git_repo / ".codebook" / "tasks"
        tasks_dir.mkdir(parents=True)
        (tasks_dir / "202412281530-EXISTING_TASK.md").write_text("Task")

        result = runner.invoke(
            main,
            ["task", "delete", "Nonexistent Task", "--force"],
        )

        assert "Task not found" in result.output
        assert "Available tasks:" in result.output

    def test_task_delete_no_tasks_dir(self, runner: CliRunner):
        """Should error when no tasks directory exists."""
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                ["task", "delete", "Any Task", "--force"],
            )

            assert "No tasks directory found" in result.output

    def test_task_delete_interactive_confirm(self, git_repo: Path):
        """Should prompt for confirmation without --force."""
        runner = CliRunner()

        tasks_dir = git_repo / ".codebook" / "tasks"
        tasks_dir.mkdir(parents=True)
        task_file = tasks_dir / "202412281530-MY_TASK.md"
        task_file.write_text("Task content")

        # Confirm deletion
        result = runner.invoke(
            main,
            ["task", "delete", "My Task"],
            input="y\n",
        )

        assert result.exit_code == 0
        assert "Deleted:" in result.output
        assert not task_file.exists()

    def test_task_delete_interactive_cancel(self, git_repo: Path):
        """Should cancel deletion when user declines."""
        runner = CliRunner()

        tasks_dir = git_repo / ".codebook" / "tasks"
        tasks_dir.mkdir(parents=True)
        task_file = tasks_dir / "202412281530-MY_TASK.md"
        task_file.write_text("Task content")

        # Decline deletion
        result = runner.invoke(
            main,
            ["task", "delete", "My Task"],
            input="n\n",
        )

        assert "Cancelled" in result.output
        assert task_file.exists()

    def test_task_delete_interactive_picker(self, git_repo: Path):
        """Should show interactive picker when no title provided."""
        runner = CliRunner()

        tasks_dir = git_repo / ".codebook" / "tasks"
        tasks_dir.mkdir(parents=True)
        task1 = tasks_dir / "202412281530-FIRST_TASK.md"
        task2 = tasks_dir / "202412281545-SECOND_TASK.md"
        task1.write_text("Task 1")
        task2.write_text("Task 2")

        # Select task 2 and confirm
        result = runner.invoke(
            main,
            ["task", "delete"],
            input="2\ny\n",
        )

        assert result.exit_code == 0
        assert "Select a task to delete:" in result.output
        assert task1.exists()
        assert not task2.exists()
