"""Tests for the CodeBook CLI interface."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from codebook.cli import _build_agent_command, main
from codebook.config import DEFAULT_REVIEW_PROMPT, AIConfig, CodeBookConfig

# Import helper from conftest (pytest loads fixtures automatically, but we need explicit import)
sys.path.insert(0, str(Path(__file__).parent))
from conftest import get_clean_git_env


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
            (test_dir / "test.md").write_text("[`old`](codebook:server.test)")

            with patch("codebook.cli.CodeBookClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.resolve_batch.return_value = {"server.test": "new"}
                mock_client_class.return_value = mock_client

                result = runner.invoke(main, ["render", "--dry-run", str(test_dir)])

                assert result.exit_code == 0
                assert "dry run" in result.output.lower()

    def test_render_reports_statistics(self, runner: CliRunner):
        """Should report rendering statistics."""
        with runner.isolated_filesystem() as tmpdir:
            test_dir = Path(tmpdir) / "codebook"
            test_dir.mkdir()
            (test_dir / "test.md").write_text("[`old`](codebook:server.test)")

            with patch("codebook.cli.CodeBookClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.resolve_batch.return_value = {"server.test": "new"}
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
            # Initialize git repo with clean environment
            env = get_clean_git_env()
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True, env=env)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmpdir,
                capture_output=True,
                env=env,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=tmpdir,
                capture_output=True,
                env=env,
            )

            # Create and commit file
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text("[`old`](codebook:server.test)")
            subprocess.run(["git", "add", "test.md"], cwd=tmpdir, capture_output=True, env=env)
            subprocess.run(
                ["git", "commit", "-m", "Initial"],
                cwd=tmpdir,
                capture_output=True,
                env=env,
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
            md_file.write_text("[`old`](codebook:server.test)")

            with patch("codebook.cli.CodeBookClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.resolve_batch.return_value = {"server.test": "new"}
                mock_client_class.return_value = mock_client

                result = runner.invoke(main, ["show", str(md_file)])

                assert result.exit_code == 0
                assert "[`new`](codebook:server.test)" in result.output

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
        """Create a temporary git repository with the CLI runner and default config."""
        with runner.isolated_filesystem() as tmpdir:
            tmpdir_path = Path(tmpdir)
            # Initialize git repo with clean environment
            env = get_clean_git_env()
            subprocess.run(
                ["git", "init", "-b", "main"], cwd=tmpdir, capture_output=True, check=True, env=env
            )
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmpdir,
                capture_output=True,
                check=True,
                env=env,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=tmpdir,
                capture_output=True,
                check=True,
                env=env,
            )
            # Create default CodeBook config
            (tmpdir_path / "codebook.yml").write_text("main_dir: .\ntasks_dir: tasks\n")
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
        tasks_dir = git_repo / "tasks"
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
        tasks_dir = git_repo / "tasks"
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
        tasks_dir = git_repo / "tasks"
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
        tasks_dir = git_repo / "tasks"
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
        tasks_dir = git_repo / "tasks"
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

        tasks_dir = git_repo / "tasks"
        tasks_dir.mkdir(parents=True)
        (tasks_dir / "20241228-OLD_FORMAT_TASK.md").write_text("Old task")

        result = runner.invoke(main, ["task", "list"])

        assert result.exit_code == 0
        assert "2024-12-28" in result.output
        assert "OLD_FORMAT_TASK" in result.output

    def test_task_delete_by_title(self, git_repo: Path):
        """Should delete task by title with --force."""
        runner = CliRunner()

        tasks_dir = git_repo / "tasks"
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

        tasks_dir = git_repo / "tasks"
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

        tasks_dir = git_repo / "tasks"
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

        tasks_dir = git_repo / "tasks"
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

        tasks_dir = git_repo / "tasks"
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

    def test_task_coverage_no_tasks(self, git_repo: Path):
        """Should error when no tasks directory exists."""
        import os

        runner = CliRunner()

        # Create tasks directory (but no task files)
        (git_repo / "tasks").mkdir(parents=True)

        old_cwd = os.getcwd()
        try:
            os.chdir(git_repo)
            result = runner.invoke(main, ["task", "coverage"])
            # When in git repo but no tasks dir, should report no commits found
            assert "No commits found in task files" in result.output
        finally:
            os.chdir(old_cwd)

    def test_task_coverage_not_git_repo(self, runner: CliRunner):
        """Should error when not in a git repository."""
        with runner.isolated_filesystem() as tmpdir:
            # Create config with main_dir and tasks_dir
            Path(tmpdir, "codebook.yml").write_text("main_dir: .\ntasks_dir: tasks\n")
            tasks_dir = Path(tmpdir) / "tasks"
            tasks_dir.mkdir(parents=True)
            (tasks_dir / "test.md").write_text("test")

            result = runner.invoke(main, ["task", "coverage"])
            assert "Not in a git repository" in result.output

    def test_task_coverage_basic(self, git_repo: Path):
        """Should calculate basic coverage statistics."""
        runner = CliRunner()

        # Create a source file and commit it
        src_file = git_repo / "src.py"
        src_file.write_text("def hello():\n    print('hello')\n")
        subprocess.run(["git", "add", "src.py"], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add hello"],
            cwd=git_repo,
            capture_output=True,
        )

        # Get the commit SHA
        result_sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        commit_sha = result_sha.stdout.strip()

        # Create a task file with the commit
        tasks_dir = git_repo / "tasks"
        tasks_dir.mkdir(parents=True)
        task_file = tasks_dir / "202412281530-ADD_HELLO.md"
        task_content = f"""# Add Hello Function

```diff
diff --git a/src.py b/src.py
index 0000000..{commit_sha}
--- a/src.py
+++ b/src.py
@@ -0,0 +1,2 @@
+def hello():
+    print('hello')
```
"""
        task_file.write_text(task_content)

        # Commit the task file so git blame can find it
        subprocess.run(["git", "add", str(task_file)], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add task"],
            cwd=git_repo,
            capture_output=True,
        )

        # Run coverage
        result = runner.invoke(main, ["task", "coverage", str(git_repo)])

        assert result.exit_code == 0
        assert "Overall Coverage:" in result.output
        assert "File Coverage:" in result.output
        assert "src.py" in result.output

    def test_task_coverage_detailed(self, git_repo: Path):
        """Should show detailed line-by-line coverage."""
        runner = CliRunner()

        # Create a source file and commit it
        src_file = git_repo / "test.py"
        src_file.write_text("line1\nline2\n")
        subprocess.run(["git", "add", "test.py"], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add test"],
            cwd=git_repo,
            capture_output=True,
        )

        # Get the commit SHA
        result_sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        commit_sha = result_sha.stdout.strip()

        # Create a task file
        tasks_dir = git_repo / "tasks"
        tasks_dir.mkdir(parents=True)
        task_file = tasks_dir / "202412281530-TEST.md"
        task_content = f"""# Test

```diff
diff --git a/test.py b/test.py
index 0000000..{commit_sha}
--- a/test.py
+++ b/test.py
@@ -0,0 +1,2 @@
+line1
+line2
```
"""
        task_file.write_text(task_content)

        # Commit the task file so git blame can find it
        subprocess.run(["git", "add", str(task_file)], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add task"],
            cwd=git_repo,
            capture_output=True,
        )

        # Run coverage with detailed flag
        result = runner.invoke(
            main,
            ["task", "coverage", str(git_repo), "--detailed"],
        )

        assert result.exit_code == 0
        assert "Detailed Line Coverage" in result.output
        assert "test.py" in result.output

    def test_task_coverage_excludes_task_files(self, git_repo: Path):
        """Should exclude task files from coverage analysis."""
        runner = CliRunner()

        # Create a source file and commit it
        src_file = git_repo / "code.py"
        src_file.write_text("print('test')\n")
        subprocess.run(["git", "add", "code.py"], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add code"],
            cwd=git_repo,
            capture_output=True,
        )

        # Get the commit SHA
        result_sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        commit_sha = result_sha.stdout.strip()

        # Create and commit a task file
        tasks_dir = git_repo / "tasks"
        tasks_dir.mkdir(parents=True)
        task_file = tasks_dir / "202412281530-TEST.md"
        task_content = f"""# Test task

```diff
diff --git a/code.py b/code.py
index 0000000..{commit_sha}
--- a/code.py
+++ b/code.py
@@ -0,0 +1 @@
+print('test')
```
"""
        task_file.write_text(task_content)
        subprocess.run(["git", "add", "-A"], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add task"],
            cwd=git_repo,
            capture_output=True,
        )

        # Run coverage
        result = runner.invoke(main, ["task", "coverage", str(git_repo)])

        # Should not analyze task files themselves
        assert result.exit_code == 0
        # Should include code.py but not the task file
        assert "code.py" in result.output
        assert "202412281530-TEST.md" not in result.output

    def test_task_coverage_short_flag(self, git_repo: Path):
        """Should show only coverage score with --short flag."""
        runner = CliRunner()

        # Create a source file and commit it
        src_file = git_repo / "test.py"
        src_file.write_text("print('hello')\n")
        subprocess.run(["git", "add", "test.py"], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add test"],
            cwd=git_repo,
            capture_output=True,
        )

        # Get the commit SHA
        result_sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        commit_sha = result_sha.stdout.strip()

        # Create a task file
        tasks_dir = git_repo / "tasks"
        tasks_dir.mkdir(parents=True)
        task_file = tasks_dir / "202412281530-TEST.md"
        task_content = f"""# Test

```diff
diff --git a/test.py b/test.py
index 0000000..{commit_sha}
--- a/test.py
+++ b/test.py
@@ -0,0 +1 @@
+print('hello')
```
"""
        task_file.write_text(task_content)

        # Commit the task file so git blame can find it
        subprocess.run(["git", "add", str(task_file)], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add task"],
            cwd=git_repo,
            capture_output=True,
        )

        # Run coverage with --short flag
        result = runner.invoke(main, ["task", "coverage", str(git_repo), "--short"])

        assert result.exit_code == 0
        # Should only show the score line
        lines = [line for line in result.output.split("\n") if line.strip()]
        # Should have extraction message and score
        assert any("Extracting commits" in line for line in lines)
        assert any("Analyzing" in line for line in lines)
        # Last non-empty line should be the score
        score_line = [line for line in lines if "%" in line and "lines)" in line][-1]
        assert "%" in score_line
        assert "lines)" in score_line
        # Should NOT have the detailed table
        assert "File Coverage:" not in result.output
        assert "====" not in result.output

    def test_task_coverage_json_flag(self, git_repo: Path):
        """Should output JSON with --json flag."""
        import json

        runner = CliRunner()

        # Create a source file and commit it
        src_file = git_repo / "test.py"
        src_file.write_text("print('hello')\n")
        subprocess.run(["git", "add", "test.py"], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add test"],
            cwd=git_repo,
            capture_output=True,
        )

        # Get the commit SHA
        result_sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        commit_sha = result_sha.stdout.strip()

        # Create a task file
        tasks_dir = git_repo / "tasks"
        tasks_dir.mkdir(parents=True)
        task_file = tasks_dir / "202412281530-TEST.md"
        task_content = f"""# Test

```diff
diff --git a/test.py b/test.py
index 0000000..{commit_sha}
--- a/test.py
+++ b/test.py
@@ -0,0 +1 @@
+print('hello')
```
"""
        task_file.write_text(task_content)

        # Commit the task file so git blame can find it
        subprocess.run(["git", "add", str(task_file)], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add task"],
            cwd=git_repo,
            capture_output=True,
        )

        # Run coverage with --json flag
        result = runner.invoke(main, ["task", "coverage", str(git_repo), "--json"])

        assert result.exit_code == 0
        # Output should be valid JSON
        data = json.loads(result.output.strip())
        assert "overall" in data
        assert "files" in data
        assert "percentage" in data["overall"]
        assert "covered" in data["overall"]
        assert "total" in data["overall"]
        # Should NOT have any non-JSON output
        assert "Extracting commits" not in result.output
        assert "Analyzing" not in result.output

    def test_task_stats_no_tasks(self, runner: CliRunner):
        """Should error when no tasks directory exists."""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["task", "stats"])
            assert "No tasks directory found" in result.output

    def test_task_stats_not_git_repo(self, runner: CliRunner):
        """Should error when not in a git repository."""
        with runner.isolated_filesystem() as tmpdir:
            # Create config with tasks_dir
            Path(tmpdir, "codebook.yml").write_text("tasks_dir: tasks\n")
            tasks_dir = Path(tmpdir) / "tasks"
            tasks_dir.mkdir(parents=True)
            (tasks_dir / "test.md").write_text("test")

            result = runner.invoke(main, ["task", "stats"])
            assert "Not in a git repository" in result.output

    def test_task_stats_basic(self, git_repo: Path):
        """Should show basic task statistics."""
        runner = CliRunner()

        # Create a source file and commit it
        src_file = git_repo / "feature.py"
        src_file.write_text("def feature():\n    return True\n")
        subprocess.run(["git", "add", "feature.py"], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add feature"],
            cwd=git_repo,
            capture_output=True,
        )

        # Get the commit SHA
        result_sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        commit_sha = result_sha.stdout.strip()

        # Create a task file
        tasks_dir = git_repo / "tasks"
        tasks_dir.mkdir(parents=True)
        task_file = tasks_dir / "202412281530-ADD_FEATURE.md"
        task_content = f"""# Add Feature

```diff
diff --git a/feature.py b/feature.py
index 0000000..{commit_sha}
--- a/feature.py
+++ b/feature.py
@@ -0,0 +1,2 @@
+def feature():
+    return True
```
"""
        task_file.write_text(task_content)

        # Run stats
        result = runner.invoke(main, ["task", "stats"])

        assert result.exit_code == 0
        assert "Task Statistics" in result.output
        assert "2024-12-28 15:30" in result.output
        assert "ADD_FEATURE" in result.output
        assert "Commits:" in result.output
        assert "Lines:" in result.output
        assert "Features:" in result.output
        assert "feature.py" in result.output

    def test_task_stats_multiple_tasks(self, git_repo: Path):
        """Should show stats for multiple tasks sorted by date."""
        runner = CliRunner()

        # Create two source files and commit them
        file1 = git_repo / "file1.py"
        file1.write_text("print('file1')\n")
        subprocess.run(["git", "add", "file1.py"], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add file1"],
            cwd=git_repo,
            capture_output=True,
        )

        file2 = git_repo / "file2.py"
        file2.write_text("print('file2')\n")
        subprocess.run(["git", "add", "file2.py"], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add file2"],
            cwd=git_repo,
            capture_output=True,
        )

        # Create task files
        tasks_dir = git_repo / "tasks"
        tasks_dir.mkdir(parents=True)

        # Earlier task
        task1 = tasks_dir / "202412281400-FIRST_TASK.md"
        task1.write_text(
            """# First Task

```diff
diff --git a/file1.py b/file1.py
--- a/file1.py
+++ b/file1.py
@@ -0,0 +1 @@
+print('file1')
```
"""
        )

        # Later task
        task2 = tasks_dir / "202412281600-SECOND_TASK.md"
        task2.write_text(
            """# Second Task

```diff
diff --git a/file2.py b/file2.py
--- a/file2.py
+++ b/file2.py
@@ -0,0 +1 @@
+print('file2')
```
"""
        )

        # Run stats
        result = runner.invoke(main, ["task", "stats"])

        assert result.exit_code == 0
        # Should show both tasks
        assert "FIRST_TASK" in result.output
        assert "SECOND_TASK" in result.output
        # Most recent first
        output_lines = result.output.split("\n")
        first_task_idx = next(i for i, line in enumerate(output_lines) if "FIRST_TASK" in line)
        second_task_idx = next(i for i, line in enumerate(output_lines) if "SECOND_TASK" in line)
        assert second_task_idx < first_task_idx  # SECOND_TASK appears first (more recent)

    def test_task_stats_multiple_files(self, git_repo: Path):
        """Should count multiple features in a single task."""
        runner = CliRunner()

        # Create multiple source files
        file1 = git_repo / "module1.py"
        file1.write_text("# Module 1\n")
        file2 = git_repo / "module2.py"
        file2.write_text("# Module 2\n")

        subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add modules"],
            cwd=git_repo,
            capture_output=True,
        )

        # Create a task file with multiple files
        tasks_dir = git_repo / "tasks"
        tasks_dir.mkdir(parents=True)
        task_file = tasks_dir / "202412281530-MULTI_FILE.md"
        task_content = """# Multi File Task

```diff
diff --git a/module1.py b/module1.py
--- a/module1.py
+++ b/module1.py
@@ -0,0 +1 @@
+# Module 1
```

```diff
diff --git a/module2.py b/module2.py
--- a/module2.py
+++ b/module2.py
@@ -0,0 +1 @@
+# Module 2
```
"""
        task_file.write_text(task_content)

        # Run stats
        result = runner.invoke(main, ["task", "stats"])

        assert result.exit_code == 0
        assert "MULTI_FILE" in result.output
        assert "Features: 2" in result.output
        assert "module1.py" in result.output
        assert "module2.py" in result.output

    def test_task_stats_empty_tasks(self, git_repo: Path):
        """Should handle tasks with no files."""
        runner = CliRunner()

        tasks_dir = git_repo / "tasks"
        tasks_dir.mkdir(parents=True)
        task_file = tasks_dir / "202412281530-EMPTY_TASK.md"
        task_file.write_text("# Empty Task\n\nNo diffs here.\n")

        result = runner.invoke(main, ["task", "stats"])

        assert result.exit_code == 0
        assert "EMPTY_TASK" in result.output
        assert "Commits:  0" in result.output
        assert "Features: 0" in result.output

    def test_task_new_with_worktree(self, git_repo: Path):
        """Should create a worktree for the task."""
        runner = CliRunner()

        # Create and commit a file
        docs_dir = git_repo / "docs"
        docs_dir.mkdir()
        doc_file = docs_dir / "readme.md"
        doc_file.write_text("Original content")
        subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=git_repo, capture_output=True)

        # Modify the file
        doc_file.write_text("Modified content")

        # Create task with worktree
        result = runner.invoke(
            main,
            ["task", "new", "Theme Support", str(docs_dir), "--worktree"],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "Created worktree" in result.output
        assert "Created task:" in result.output

        # Verify worktree was created
        # Expected format: {rootdir}-theme_support
        root_dir_name = git_repo.name
        expected_worktree_name = f"{root_dir_name}-theme_support"
        worktree_path = git_repo.parent / expected_worktree_name

        assert worktree_path.exists(), f"Worktree directory not found at {worktree_path}"

        # Verify task file was created in worktree
        worktree_tasks_dir = worktree_path / "tasks"
        assert worktree_tasks_dir.exists()
        task_files = list(worktree_tasks_dir.glob("*THEME_SUPPORT.md"))
        assert len(task_files) == 1

        # Verify task contains the diff
        task_content = task_files[0].read_text()
        assert "```diff" in task_content
        assert "Modified content" in task_content

        # Verify original branch has changes reverted
        original_content = doc_file.read_text()
        assert original_content == "Original content"

        # Verify worktree has the modified content
        worktree_doc = worktree_path / "docs" / "readme.md"
        assert worktree_doc.exists()
        worktree_content = worktree_doc.read_text()
        assert worktree_content == "Modified content"

        # Clean up worktree
        subprocess.run(
            ["git", "worktree", "remove", str(worktree_path), "--force"],
            cwd=git_repo,
            capture_output=True,
        )

    def test_task_new_with_worktree_untracked_files(self, git_repo: Path):
        """Should handle untracked files in worktree."""
        runner = CliRunner()

        # Create docs directory with initial commit
        docs_dir = git_repo / "docs"
        docs_dir.mkdir()
        initial_file = docs_dir / "initial.md"
        initial_file.write_text("Initial content")
        subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=git_repo, capture_output=True)

        # Create an untracked file
        new_doc = docs_dir / "new_feature.md"
        new_doc.write_text("New feature documentation")

        # Create task with worktree
        result = runner.invoke(
            main,
            ["task", "new", "New Feature", str(docs_dir), "--worktree"],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "Created worktree" in result.output

        # Verify worktree was created
        # Expected format: {rootdir}-new_feature
        root_dir_name = git_repo.name
        expected_worktree_name = f"{root_dir_name}-new_feature"
        worktree_path = git_repo.parent / expected_worktree_name

        assert worktree_path.exists(), f"Worktree directory not found at {worktree_path}"

        # Verify untracked file was removed from source
        assert not new_doc.exists()

        # Verify untracked file exists in worktree
        worktree_doc = worktree_path / "docs" / "new_feature.md"
        assert worktree_doc.exists()
        assert worktree_doc.read_text() == "New feature documentation"

        # Clean up worktree
        subprocess.run(
            ["git", "worktree", "remove", str(worktree_path), "--force"],
            cwd=git_repo,
            capture_output=True,
        )

    def test_task_new_with_worktree_no_changes(self, git_repo: Path):
        """Should handle case with no uncommitted changes."""
        runner = CliRunner()

        # Create and commit a file (no modifications)
        docs_dir = git_repo / "docs"
        docs_dir.mkdir()
        doc_file = docs_dir / "readme.md"
        doc_file.write_text("Committed content")
        subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=git_repo, capture_output=True)

        # Try to create task with worktree (no changes)
        result = runner.invoke(
            main,
            ["task", "new", "No Changes", str(docs_dir), "--worktree"],
            catch_exceptions=False,
        )

        # Should still create worktree but report no modified files
        assert "Created worktree" in result.output
        assert "No modified markdown files found" in result.output

        # Clean up any created worktree
        root_dir_name = git_repo.name
        expected_worktree_name = f"{root_dir_name}-no_changes"
        worktree_path = git_repo.parent / expected_worktree_name
        if worktree_path.exists():
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_path), "--force"],
                cwd=git_repo,
                capture_output=True,
            )

    def test_task_update_help(self, runner: CliRunner):
        """Should show task update help."""
        result = runner.invoke(main, ["task", "update", "--help"])

        assert result.exit_code == 0
        assert "Update a task file" in result.output

    def test_task_update_adds_new_diff(self, git_repo: Path):
        """Should add new diffs to existing task file."""
        runner = CliRunner()

        # Create and commit initial files
        docs_dir = git_repo / "docs"
        docs_dir.mkdir()
        doc1 = docs_dir / "doc1.md"
        doc1.write_text("Original doc1")
        subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=git_repo, capture_output=True)

        # Modify doc1
        doc1.write_text("Modified doc1")

        # Create initial task
        result = runner.invoke(
            main,
            ["task", "new", "Initial Task", str(docs_dir)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        # Commit doc1 changes and task
        subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Doc1 update"], cwd=git_repo, capture_output=True)

        # Add doc2 (new file)
        doc2 = docs_dir / "doc2.md"
        doc2.write_text("New doc2 content")

        # Find the task file
        tasks_dir = git_repo / "tasks"
        task_files = list(tasks_dir.glob("*INITIAL_TASK.md"))
        assert len(task_files) == 1
        task_file = task_files[0]

        # Update task with new docs
        result = runner.invoke(
            main,
            ["task", "update", str(task_file), str(docs_dir)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "Updated task:" in result.output
        assert "+1 added" in result.output

        # Verify task contains both diffs
        content = task_file.read_text()
        assert "doc1.md" in content
        assert "doc2.md" in content
        assert "New doc2 content" in content

    def test_task_update_updates_existing_files(self, git_repo: Path):
        """Should update diffs for files already in the task."""
        runner = CliRunner()

        # Create and commit initial files
        docs_dir = git_repo / "docs"
        docs_dir.mkdir()
        doc1 = docs_dir / "doc1.md"
        doc1.write_text("Original doc1")
        subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=git_repo, capture_output=True)

        # Modify doc1
        doc1.write_text("Modified doc1")

        # Create task
        result = runner.invoke(
            main,
            ["task", "new", "My Task", str(docs_dir)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        # Find task file
        tasks_dir = git_repo / "tasks"
        task_files = list(tasks_dir.glob("*MY_TASK.md"))
        task_file = task_files[0]

        # Verify initial content
        initial_content = task_file.read_text()
        assert "Modified doc1" in initial_content

        # Modify doc1 again (file already in task)
        doc1.write_text("Further modified doc1")

        # Update task - should update existing diff
        result = runner.invoke(
            main,
            ["task", "update", str(task_file), str(docs_dir)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "~1 updated" in result.output

        # Verify task contains the new diff content
        updated_content = task_file.read_text()
        assert "Further modified doc1" in updated_content

    def test_task_update_preserves_footer(self, git_repo: Path):
        """Should insert diffs before footer markers."""
        runner = CliRunner()

        # Create and commit initial file
        docs_dir = git_repo / "docs"
        docs_dir.mkdir()
        doc1 = docs_dir / "doc1.md"
        doc1.write_text("Original")
        subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=git_repo, capture_output=True)

        # Create task file with footer manually
        tasks_dir = git_repo / "tasks"
        tasks_dir.mkdir(parents=True)
        task_file = tasks_dir / "202412281530-TEST_TASK.md"
        task_file.write_text(
            """# Test Task

--- NOTES ---
Some notes here
"""
        )

        # Modify doc1
        doc1.write_text("Modified")

        # Update task
        result = runner.invoke(
            main,
            ["task", "update", str(task_file), str(docs_dir)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        # Verify footer is preserved at end
        content = task_file.read_text()
        assert "--- NOTES ---" in content
        assert "Some notes here" in content
        # Diff should be before notes
        notes_pos = content.find("--- NOTES ---")
        diff_pos = content.find("```diff")
        assert diff_pos < notes_pos

    def test_task_update_with_directory_scope(self, git_repo: Path):
        """Should update with multiple files from directory scope."""
        runner = CliRunner()

        # Create and commit initial file
        docs_dir = git_repo / "docs"
        docs_dir.mkdir()
        doc1 = docs_dir / "doc1.md"
        doc1.write_text("Original doc1")
        subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=git_repo, capture_output=True)

        # Create task file
        tasks_dir = git_repo / "tasks"
        tasks_dir.mkdir(parents=True)
        task_file = tasks_dir / "202412281530-DOCS_UPDATE.md"
        task_file.write_text("# Docs Update\n\n")

        # Add multiple new docs
        doc2 = docs_dir / "doc2.md"
        doc2.write_text("New doc2")
        doc3 = docs_dir / "doc3.md"
        doc3.write_text("New doc3")

        # Update task
        result = runner.invoke(
            main,
            ["task", "update", str(task_file), str(docs_dir)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "+2 added" in result.output

        content = task_file.read_text()
        assert "doc2.md" in content
        assert "doc3.md" in content

    def test_task_update_no_args_finds_no_files(self, git_repo: Path):
        """Should report no files when no modified/untracked task files exist."""
        runner = CliRunner()

        # Create tasks directory with no modified files
        tasks_dir = git_repo / "codebook" / "tasks"
        tasks_dir.mkdir(parents=True)

        # Create codebook.yml
        config_file = git_repo / "codebook.yml"
        config_file.write_text("main_dir: codebook\n")

        result = runner.invoke(main, ["task", "update"])

        assert result.exit_code == 0
        assert "No modified or untracked task files" in result.output

    def test_task_update_no_args_with_untracked_task_files(self, git_repo: Path):
        """Should find and update untracked task files."""
        runner = CliRunner()

        # Create main_dir with a doc file
        main_dir = git_repo / "codebook"
        main_dir.mkdir(parents=True)
        doc1 = main_dir / "doc1.md"
        doc1.write_text("Original doc")
        subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=git_repo, capture_output=True)

        # Create tasks directory with an untracked task file
        tasks_dir = main_dir / "tasks"
        tasks_dir.mkdir()
        task_file = tasks_dir / "202412281530-TEST.md"
        task_file.write_text("# Test Task\n\n")

        # Create codebook.yml
        config_file = git_repo / "codebook.yml"
        config_file.write_text("main_dir: codebook\n")

        result = runner.invoke(main, ["task", "update"])

        # Should find 1 untracked task file
        assert "Found 1 task file(s) to update:" in result.output
        assert "TEST.md" in result.output

    def test_task_update_no_args_uses_default_scope(self, git_repo: Path):
        """Should use main_dir from config as default scope."""
        runner = CliRunner()

        # Create main_dir with a modified doc file
        main_dir = git_repo / "codebook"
        main_dir.mkdir(parents=True)
        doc1 = main_dir / "doc1.md"
        doc1.write_text("Original doc")
        subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=git_repo, capture_output=True)

        # Create tasks directory with an untracked task file
        tasks_dir = main_dir / "tasks"
        tasks_dir.mkdir()
        task_file = tasks_dir / "202412281530-TEST.md"
        task_file.write_text("# Test Task\n\n")

        # Modify doc1
        doc1.write_text("Modified doc")

        # Create codebook.yml
        config_file = git_repo / "codebook.yml"
        config_file.write_text("main_dir: codebook\n")

        result = runner.invoke(main, ["task", "update"])

        # Should find and update the task file
        assert "Found 1 task file(s) to update:" in result.output
        # Should pick up the modified doc
        content = task_file.read_text()
        assert "doc1.md" in content or "Updated task" in result.output


class TestAICommands:
    """Tests for AI helper commands."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def ai_review_env(self, runner: CliRunner):
        """Set up environment for AI review tests with task file and mocked subprocess.

        Yields a tuple of (runner, task_file, mock_run) for use in tests.
        """
        from contextlib import contextmanager

        @contextmanager
        def create_env(task_content: str = "Task content"):
            with runner.isolated_filesystem() as tmpdir:
                task_file = Path(tmpdir) / "task.md"
                task_file.write_text(task_content)

                with patch("codebook.cli.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)
                    yield runner, task_file, mock_run

        return create_env

    def test_ai_help_command(self, runner: CliRunner):
        """Should show help for AI helpers."""
        result = runner.invoke(main, ["ai", "help"])

        assert result.exit_code == 0
        assert "CodeBook AI Helpers" in result.output
        assert "Available commands:" in result.output
        assert "Supported agents:" in result.output
        assert "claude" in result.output
        assert "codex" in result.output
        assert "gemini" in result.output
        assert "opencode" in result.output
        assert "kimi" in result.output

    def test_ai_group_help(self, runner: CliRunner):
        """Should show AI group help."""
        result = runner.invoke(main, ["ai", "--help"])

        assert result.exit_code == 0
        assert "AI helpers for CodeBook tasks" in result.output
        assert "help" in result.output
        assert "review" in result.output

    def test_ai_review_help(self, runner: CliRunner):
        """Should show review command help."""
        result = runner.invoke(main, ["ai", "review", "--help"])

        assert result.exit_code == 0
        assert "Review a task with an AI agent" in result.output
        assert "AGENT" in result.output
        assert "PATH" in result.output

    def test_ai_review_requires_agent(self, runner: CliRunner):
        """Should require agent argument."""
        result = runner.invoke(main, ["ai", "review"])

        assert result.exit_code != 0
        assert "Missing argument" in result.output or "AGENT" in result.output

    def test_ai_review_invalid_agent(self, runner: CliRunner):
        """Should reject invalid agent."""
        with runner.isolated_filesystem() as tmpdir:
            task_file = Path(tmpdir) / "task.md"
            task_file.write_text("Task content")

            result = runner.invoke(main, ["ai", "review", "invalid_agent", str(task_file)])

            assert result.exit_code != 0
            assert "Invalid value" in result.output or "invalid_agent" in result.output

    def test_ai_review_no_path_finds_no_files(self, runner: CliRunner):
        """Should report no files when no modified/untracked files exist."""
        with runner.isolated_filesystem() as tmpdir:
            # Create tasks directory with no modified files
            tasks_dir = Path(tmpdir) / "codebook" / "tasks"
            tasks_dir.mkdir(parents=True)

            # Create codebook.yml
            config_file = Path(tmpdir) / "codebook.yml"
            config_file.write_text("main_dir: codebook\n")

            # Initialize git repo and commit the task file
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

            result = runner.invoke(main, ["ai", "review", "claude"])

            assert result.exit_code == 0
            assert "No modified or untracked" in result.output

    def test_ai_review_path_must_exist(self, runner: CliRunner):
        """Should require path to exist."""
        result = runner.invoke(main, ["ai", "review", "claude", "/nonexistent/path.md"])

        assert result.exit_code != 0

    def test_ai_review_claude_command(self, runner: CliRunner):
        """Should build correct command for claude agent."""
        with runner.isolated_filesystem() as tmpdir:
            task_file = Path(tmpdir) / "task.md"
            task_file.write_text("Task content")

            with patch("codebook.cli.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                runner.invoke(
                    main,
                    ["ai", "review", "claude", str(task_file)],
                    catch_exceptions=False,
                )

                # Check that subprocess.run was called
                mock_run.assert_called_once()
                cmd = mock_run.call_args[0][0]

                # Verify command structure
                assert cmd[0] == "claude"
                assert "--print" in cmd
                # Prompt should contain task file path
                prompt_idx = cmd.index("--print") + 1
                assert str(task_file.resolve()) in cmd[prompt_idx]

    def test_ai_review_codex_command(self, runner: CliRunner):
        """Should build correct command for codex agent."""
        with runner.isolated_filesystem() as tmpdir:
            task_file = Path(tmpdir) / "task.md"
            task_file.write_text("Task content")

            with patch("codebook.cli.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                runner.invoke(
                    main,
                    ["ai", "review", "codex", str(task_file)],
                    catch_exceptions=False,
                )

                mock_run.assert_called_once()
                cmd = mock_run.call_args[0][0]
                assert cmd[0] == "codex"

    def test_ai_review_gemini_command(self, runner: CliRunner):
        """Should build correct command for gemini agent."""
        with runner.isolated_filesystem() as tmpdir:
            task_file = Path(tmpdir) / "task.md"
            task_file.write_text("Task content")

            with patch("codebook.cli.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                runner.invoke(
                    main,
                    ["ai", "review", "gemini", str(task_file)],
                    catch_exceptions=False,
                )

                mock_run.assert_called_once()
                cmd = mock_run.call_args[0][0]
                assert cmd[0] == "gemini"

    def test_ai_review_opencode_command(self, runner: CliRunner):
        """Should build correct command for opencode agent."""
        with runner.isolated_filesystem() as tmpdir:
            task_file = Path(tmpdir) / "task.md"
            task_file.write_text("Task content")

            with patch("codebook.cli.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                runner.invoke(
                    main,
                    ["ai", "review", "opencode", str(task_file)],
                    catch_exceptions=False,
                )

                mock_run.assert_called_once()
                cmd = mock_run.call_args[0][0]
                assert cmd[0] == "opencode"

    def test_ai_review_kimi_command(self, runner: CliRunner):
        """Should build correct command for kimi agent."""
        with runner.isolated_filesystem() as tmpdir:
            task_file = Path(tmpdir) / "task.md"
            task_file.write_text("Task content")

            with patch("codebook.cli.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                runner.invoke(
                    main,
                    ["ai", "review", "kimi", str(task_file)],
                    catch_exceptions=False,
                )

                mock_run.assert_called_once()
                cmd = mock_run.call_args[0][0]
                assert cmd[0] == "kimi"

    def test_ai_review_agent_not_found(self, runner: CliRunner):
        """Should error when agent is not installed."""
        with runner.isolated_filesystem() as tmpdir:
            task_file = Path(tmpdir) / "task.md"
            task_file.write_text("Task content")

            with patch("codebook.cli.subprocess.run") as mock_run:
                mock_run.side_effect = FileNotFoundError("Agent not found")

                result = runner.invoke(
                    main,
                    ["ai", "review", "claude", str(task_file)],
                )

                assert result.exit_code != 0
                assert "not found" in result.output.lower()

    def test_ai_review_with_agent_args(self, runner: CliRunner):
        """Should pass additional arguments to agent before the prompt."""
        with runner.isolated_filesystem() as tmpdir:
            task_file = Path(tmpdir) / "task.md"
            task_file.write_text("Task content")

            with patch("codebook.cli.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                runner.invoke(
                    main,
                    ["ai", "review", "gemini", str(task_file), "--", "--model", "gemini-pro"],
                    catch_exceptions=False,
                )

                mock_run.assert_called_once()
                cmd = mock_run.call_args[0][0]
                assert "--model" in cmd
                assert "gemini-pro" in cmd
                # Args should come before --prompt-interactive (the prompt flag)
                model_idx = cmd.index("--model")
                prompt_idx = cmd.index("--prompt-interactive")
                assert model_idx < prompt_idx, "agent_args should come before the prompt"

    def test_ai_review_prompt_contains_task_path(self, runner: CliRunner):
        """Should include task path in prompt."""
        with runner.isolated_filesystem() as tmpdir:
            task_file = Path(tmpdir) / "task.md"
            task_file.write_text("Task content")

            with patch("codebook.cli.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                runner.invoke(
                    main,
                    ["ai", "review", "claude", str(task_file)],
                    catch_exceptions=False,
                )

                mock_run.assert_called_once()
                cmd = mock_run.call_args[0][0]
                # The prompt should contain the resolved task file path
                prompt_idx = cmd.index("--print") + 1
                prompt = cmd[prompt_idx]
                assert str(task_file.resolve()) in prompt

    def test_ai_review_verbose_shows_command(self, runner: CliRunner):
        """Should show command when verbose is enabled."""
        with runner.isolated_filesystem() as tmpdir:
            task_file = Path(tmpdir) / "task.md"
            task_file.write_text("Task content")

            with patch("codebook.cli.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                result = runner.invoke(
                    main,
                    ["--verbose", "ai", "review", "claude", str(task_file)],
                    catch_exceptions=False,
                )

                assert "Command:" in result.output

    def test_ai_review_propagates_exit_code(self, runner: CliRunner):
        """Should propagate agent exit code."""
        with runner.isolated_filesystem() as tmpdir:
            task_file = Path(tmpdir) / "task.md"
            task_file.write_text("Task content")

            with patch("codebook.cli.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=42)

                result = runner.invoke(
                    main,
                    ["ai", "review", "claude", str(task_file)],
                )

                assert result.exit_code == 42

    def test_ai_review_custom_prompt_from_config(self, runner: CliRunner):
        """Should use custom review_prompt from config file."""
        with runner.isolated_filesystem() as tmpdir:
            task_file = Path(tmpdir) / "task.md"
            task_file.write_text("Task content")

            # Create a custom config with a custom review prompt
            config_file = Path(tmpdir) / "codebook.yml"
            config_file.write_text(
                "ai:\n" "  review_prompt: 'Custom prompt for [TASK_FILE] review'\n"
            )

            with patch("codebook.cli.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                # Change to the directory with the config
                import os

                original_cwd = os.getcwd()
                try:
                    os.chdir(tmpdir)
                    runner.invoke(
                        main,
                        ["ai", "review", "claude", str(task_file)],
                        catch_exceptions=False,
                    )
                finally:
                    os.chdir(original_cwd)

                mock_run.assert_called_once()
                cmd = mock_run.call_args[0][0]
                prompt_idx = cmd.index("--print") + 1
                prompt = cmd[prompt_idx]
                # Verify custom prompt is used and placeholder is replaced
                assert "Custom prompt for" in prompt
                assert str(task_file.resolve()) in prompt

    def test_ai_review_rejects_directory(self, runner: CliRunner):
        """Should reject directory as path argument."""
        with runner.isolated_filesystem() as tmpdir:
            result = runner.invoke(main, ["ai", "review", "claude", tmpdir])

            assert result.exit_code != 0
            assert "directory" in result.output.lower() or "file" in result.output.lower()

    def test_ai_review_generic_exception(self, runner: CliRunner):
        """Should handle generic exceptions from subprocess.run."""
        with runner.isolated_filesystem() as tmpdir:
            task_file = Path(tmpdir) / "task.md"
            task_file.write_text("Task content")

            with patch("codebook.cli.subprocess.run") as mock_run:
                mock_run.side_effect = RuntimeError("Something went wrong")

                result = runner.invoke(
                    main,
                    ["ai", "review", "claude", str(task_file)],
                )

                assert result.exit_code == 1
                assert "Error running agent:" in result.output

    def test_ai_review_no_path_with_untracked_files(self, runner: CliRunner):
        """Should find and review untracked markdown files in tasks directory."""
        with runner.isolated_filesystem() as tmpdir:
            # Create tasks directory with untracked files
            tasks_dir = Path(tmpdir) / "codebook" / "tasks"
            tasks_dir.mkdir(parents=True)

            task1 = tasks_dir / "202512281502-task1.md"
            task1.write_text("Task 1 content")

            task2 = tasks_dir / "202512281503-task2.md"
            task2.write_text("Task 2 content")

            # Create codebook.yml
            config_file = Path(tmpdir) / "codebook.yml"
            config_file.write_text("main_dir: codebook\n")

            # Initialize git repo (files are untracked)
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

            # Mock only _run_agent_review to avoid affecting git commands
            with patch("codebook.cli._run_agent_review") as mock_review:
                mock_review.return_value = 0

                result = runner.invoke(main, ["ai", "review", "claude"])

                # Should have found 2 files
                assert "Found 2 task file(s) to review:" in result.output
                assert "task1.md" in result.output
                assert "task2.md" in result.output
                # Should have called review for each file
                assert mock_review.call_count == 2

    def test_ai_review_no_path_with_modified_files(self, runner: CliRunner):
        """Should find and review modified markdown files in tasks directory."""
        with runner.isolated_filesystem() as tmpdir:
            # Create tasks directory
            tasks_dir = Path(tmpdir) / "codebook" / "tasks"
            tasks_dir.mkdir(parents=True)

            task1 = tasks_dir / "202512281502-task1.md"
            task1.write_text("Task 1 original")

            # Create codebook.yml
            config_file = Path(tmpdir) / "codebook.yml"
            config_file.write_text("main_dir: codebook\n")

            # Initialize git repo and commit
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
            subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial"],
                cwd=tmpdir,
                capture_output=True,
            )

            # Modify the file
            task1.write_text("Task 1 modified")

            # Mock only _run_agent_review to avoid affecting git commands
            with patch("codebook.cli._run_agent_review") as mock_review:
                mock_review.return_value = 0

                result = runner.invoke(main, ["ai", "review", "claude"])

                # Should have found 1 modified file
                assert "Found 1 task file(s) to review:" in result.output
                assert "task1.md" in result.output
                assert mock_review.call_count == 1

    def test_ai_review_no_path_reviews_all_files(self, runner: CliRunner):
        """Should review all found task files sequentially."""
        with runner.isolated_filesystem() as tmpdir:
            # Create tasks directory with untracked files
            tasks_dir = Path(tmpdir) / "codebook" / "tasks"
            tasks_dir.mkdir(parents=True)

            task1 = tasks_dir / "202512281502-task1.md"
            task1.write_text("Task 1")
            task2 = tasks_dir / "202512281503-task2.md"
            task2.write_text("Task 2")

            # Create codebook.yml
            config_file = Path(tmpdir) / "codebook.yml"
            config_file.write_text("main_dir: codebook\n")

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

            # Mock only _run_agent_review to avoid affecting git commands
            with patch("codebook.cli._run_agent_review") as mock_review:
                mock_review.return_value = 0

                runner.invoke(main, ["ai", "review", "claude"])

                # Should have called _run_agent_review for each file
                assert mock_review.call_count == 2

    def test_ai_review_no_path_propagates_failure(self, runner: CliRunner):
        """Should propagate non-zero exit code when any review fails."""
        with runner.isolated_filesystem() as tmpdir:
            # Create tasks directory with untracked files
            tasks_dir = Path(tmpdir) / "codebook" / "tasks"
            tasks_dir.mkdir(parents=True)

            task1 = tasks_dir / "task1.md"
            task1.write_text("Task 1")
            task2 = tasks_dir / "task2.md"
            task2.write_text("Task 2")

            # Create codebook.yml
            config_file = Path(tmpdir) / "codebook.yml"
            config_file.write_text("main_dir: codebook\n")

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

            # Mock only _run_agent_review to avoid affecting git commands
            with patch("codebook.cli._run_agent_review") as mock_review:
                # First call succeeds, second fails
                mock_review.side_effect = [0, 1]

                result = runner.invoke(main, ["ai", "review", "claude"])

                assert result.exit_code == 1


class TestBuildAgentCommand:
    """Tests for _build_agent_command function."""

    def test_unsupported_agent_returns_none(self):
        """Should return None for unsupported agent."""
        result = _build_agent_command("unsupported_agent", "test prompt", ())
        assert result is None

    def test_claude_command_structure(self):
        """Should build correct claude command."""
        result = _build_agent_command("claude", "test prompt", ())
        assert result == ["claude", "--print", "test prompt"]

    def test_codex_command_structure(self):
        """Should build correct codex command with prompt as positional arg."""
        result = _build_agent_command("codex", "test prompt", ())
        assert result == ["codex", "test prompt"]

    def test_gemini_command_structure(self):
        """Should build correct gemini command."""
        result = _build_agent_command("gemini", "test prompt", ())
        assert result == ["gemini", "--prompt-interactive", "test prompt"]

    def test_opencode_command_structure(self):
        """Should build correct opencode command with prompt as positional arg."""
        result = _build_agent_command("opencode", "test prompt", ())
        assert result == ["opencode", "test prompt"]

    def test_kimi_command_structure(self):
        """Should build correct kimi command."""
        result = _build_agent_command("kimi", "test prompt", ())
        assert result == ["kimi", "--command", "test prompt"]

    def test_agent_args_inserted_before_prompt_flag(self):
        """Should insert agent_args before the prompt flag."""
        result = _build_agent_command("claude", "test prompt", ("--model", "gpt-4"))
        assert result == ["claude", "--model", "gpt-4", "--print", "test prompt"]

    def test_agent_args_inserted_before_positional_prompt(self):
        """Should insert agent_args before positional prompt."""
        result = _build_agent_command("codex", "test prompt", ("--flag", "value"))
        assert result == ["codex", "--flag", "value", "test prompt"]


class TestAIConfig:
    """Tests for AI helper configuration (serialization/deserialization)."""

    def test_from_dict_sets_custom_review_prompt(self):
        """_from_dict should apply a custom ai.review_prompt from config dict."""
        config_dict = {
            "ai": {
                "review_prompt": "Custom review prompt for PR reviews.",
            }
        }

        cfg = CodeBookConfig._from_dict(config_dict)

        assert cfg.ai.review_prompt == "Custom review prompt for PR reviews."

    def test_from_dict_uses_default_when_not_specified(self):
        """_from_dict should use DEFAULT_REVIEW_PROMPT when ai.review_prompt not specified."""
        cfg = CodeBookConfig._from_dict({})

        assert cfg.ai.review_prompt == DEFAULT_REVIEW_PROMPT

    def test_to_dict_omits_ai_when_review_prompt_is_default(self):
        """to_dict() should omit the 'ai' key when the review_prompt is the default."""
        cfg = CodeBookConfig._from_dict({})

        # Sanity-check default wiring
        assert cfg.ai.review_prompt == DEFAULT_REVIEW_PROMPT

        data = cfg.to_dict()

        assert "ai" not in data

    def test_to_dict_includes_ai_when_review_prompt_overridden(self):
        """to_dict() should include 'ai.review_prompt' when it differs from default."""
        config_dict = {
            "ai": {
                "review_prompt": "Overridden review prompt.",
            }
        }
        cfg = CodeBookConfig._from_dict(config_dict)

        # Ensure we really have a non-default prompt
        assert cfg.ai.review_prompt != DEFAULT_REVIEW_PROMPT

        data = cfg.to_dict()

        assert "ai" in data
        assert data["ai"]["review_prompt"] == "Overridden review prompt."

    def test_ai_config_default_initialization(self):
        """AIConfig should initialize with default review prompt."""
        ai_config = AIConfig()
        assert ai_config.review_prompt == DEFAULT_REVIEW_PROMPT
