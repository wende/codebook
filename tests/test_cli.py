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
            md_file.write_text("[`old`](codebook:server.test)")
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

    def test_task_coverage_no_tasks(self, runner: CliRunner):
        """Should error when no tasks directory exists."""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["task", "coverage"])
            assert "No tasks directory found" in result.output

    def test_task_coverage_not_git_repo(self, runner: CliRunner):
        """Should error when not in a git repository."""
        with runner.isolated_filesystem() as tmpdir:
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

    def test_task_stats_no_tasks(self, runner: CliRunner):
        """Should error when no tasks directory exists."""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["task", "stats"])
            assert "No tasks directory found" in result.output

    def test_task_stats_not_git_repo(self, runner: CliRunner):
        """Should error when not in a git repository."""
        with runner.isolated_filesystem() as tmpdir:
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
        task1.write_text("""# First Task

```diff
diff --git a/file1.py b/file1.py
--- a/file1.py
+++ b/file1.py
@@ -0,0 +1 @@
+print('file1')
```
""")

        # Later task
        task2 = tasks_dir / "202412281600-SECOND_TASK.md"
        task2.write_text("""# Second Task

```diff
diff --git a/file2.py b/file2.py
--- a/file2.py
+++ b/file2.py
@@ -0,0 +1 @@
+print('file2')
```
""")

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
