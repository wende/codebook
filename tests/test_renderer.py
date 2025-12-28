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
        md_file.write_text("[`value`](codebook:server.test)")
        mock_client.resolve_batch.return_value = {"server.test": "resolved"}

        result = renderer.render_file(md_file)

        assert result.templates_found == 1
        mock_client.resolve_batch.assert_called_once_with(["server.test"])

    def test_render_file_updates_values(
        self,
        renderer: CodeBookRenderer,
        mock_client: MagicMock,
        temp_dir: Path,
    ):
        """Should update file with resolved values."""
        md_file = temp_dir / "test.md"
        md_file.write_text("[`old`](codebook:server.test)")
        mock_client.resolve_batch.return_value = {"server.test": "new"}

        result = renderer.render_file(md_file)

        assert result.changed is True
        assert result.templates_resolved == 1
        assert md_file.read_text() == "[`new`](codebook:server.test)"

    def test_render_file_dry_run_does_not_modify(
        self,
        renderer: CodeBookRenderer,
        mock_client: MagicMock,
        temp_dir: Path,
    ):
        """Should not modify file in dry run mode."""
        md_file = temp_dir / "test.md"
        md_file.write_text("[`old`](codebook:server.test)")
        mock_client.resolve_batch.return_value = {"server.test": "new"}

        result = renderer.render_file(md_file, dry_run=True)

        assert result.changed is True
        assert md_file.read_text() == "[`old`](codebook:server.test)"  # Unchanged

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
        md_file.write_text("[`old`](codebook:server.test)")
        mock_client.resolve_batch.return_value = {"server.test": "new"}

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
        md_file.write_text("[`old`](codebook:server.test)")
        mock_client.resolve_batch.return_value = {}  # No values returned

        result = renderer.render_file(md_file)

        assert result.templates_found == 1
        assert result.templates_resolved == 0
        assert result.changed is False
        assert md_file.read_text() == "[`old`](codebook:server.test)"

    def test_render_file_partial_resolution(
        self,
        renderer: CodeBookRenderer,
        mock_client: MagicMock,
        temp_dir: Path,
    ):
        """Should update only successfully resolved templates."""
        md_file = temp_dir / "test.md"
        md_file.write_text("[`a`](codebook:server.first) and [`b`](codebook:server.second)")
        mock_client.resolve_batch.return_value = {"server.first": "X"}  # Only one resolved

        result = renderer.render_file(md_file)

        assert result.templates_found == 2
        assert result.templates_resolved == 1
        assert result.changed is True
        assert md_file.read_text() == "[`X`](codebook:server.first) and [`b`](codebook:server.second)"

    def test_render_directory_processes_all_md_files(
        self,
        renderer: CodeBookRenderer,
        mock_client: MagicMock,
        temp_dir: Path,
    ):
        """Should process all markdown files in directory."""
        (temp_dir / "file1.md").write_text("[`a`](codebook:server.test)")
        (temp_dir / "file2.md").write_text("[`b`](codebook:server.test)")
        (temp_dir / "file3.txt").write_text("[`c`](codebook:server.test)")  # Not .md
        mock_client.resolve_batch.return_value = {"server.test": "new"}

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
        (temp_dir / "root.md").write_text("[`a`](codebook:server.test)")
        (subdir / "nested.md").write_text("[`b`](codebook:server.test)")
        mock_client.resolve_batch.return_value = {"server.test": "new"}

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
        (temp_dir / "root.md").write_text("[`a`](codebook:server.test)")
        (subdir / "nested.md").write_text("[`b`](codebook:server.test)")
        mock_client.resolve_batch.return_value = {"server.test": "new"}

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
        content = "[`old`](codebook:server.test)"
        mock_client.resolve_batch.return_value = {"server.test": "new"}

        rendered, values = renderer.render_content(content)

        assert rendered == "[`new`](codebook:server.test)"
        assert values == {"server.test": "new"}

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
        content = "[`old`](codebook:server.test)"
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

Some text before [`value`](codebook:server.test) and after.

## Subheader

More content.
"""
        md_file.write_text(content)
        mock_client.resolve_batch.return_value = {"server.test": "NEW"}

        renderer.render_file(md_file)

        result = md_file.read_text()
        assert "# Header" in result
        assert "## Subheader" in result
        assert "[`NEW`](codebook:server.test)" in result


class TestBacklinkUpdates:
    """Tests for bidirectional link/backlink functionality."""

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

    def test_render_finds_markdown_links(
        self,
        renderer: CodeBookRenderer,
        temp_dir: Path,
    ):
        """Should count markdown links to .md files."""
        md_file = temp_dir / "source.md"
        md_file.write_text("[Link](other.md)")

        result = renderer.render_file(md_file, dry_run=True)

        assert result.backlinks_found == 1

    def test_render_creates_backlink_in_target(
        self,
        renderer: CodeBookRenderer,
        temp_dir: Path,
    ):
        """Should create backlink in target file."""
        source = temp_dir / "source.md"
        target = temp_dir / "target.md"

        source.write_text("[Link to Target](target.md)")
        target.write_text("# Target Document\n\nSome content.")

        renderer.render_file(source)

        target_content = target.read_text()
        assert "--- BACKLINKS ---" in target_content
        assert 'source.md "codebook:backlink")' in target_content

    def test_render_appends_to_existing_backlinks(
        self,
        renderer: CodeBookRenderer,
        temp_dir: Path,
    ):
        """Should append to existing BACKLINKS section."""
        source = temp_dir / "source.md"
        target = temp_dir / "target.md"

        source.write_text("[New Link](target.md)")
        target.write_text(
            '# Target\n\n--- BACKLINKS ---\n[Old](old.md "codebook:backlink")\n'
        )

        renderer.render_file(source)

        target_content = target.read_text()
        assert '[Old](old.md "codebook:backlink")' in target_content
        assert 'source.md "codebook:backlink")' in target_content

    def test_render_does_not_duplicate_backlinks(
        self,
        renderer: CodeBookRenderer,
        temp_dir: Path,
    ):
        """Should not add duplicate backlinks."""
        source = temp_dir / "source.md"
        target = temp_dir / "target.md"

        source.write_text("[Link](target.md)")
        target.write_text(
            '# Target\n\n--- BACKLINKS ---\n[Link](source.md "codebook:backlink")\n'
        )

        renderer.render_file(source)

        target_content = target.read_text()
        # Count occurrences of source.md backlink
        count = target_content.count('source.md "codebook:backlink")')
        assert count == 1

    def test_dry_run_does_not_update_backlinks(
        self,
        renderer: CodeBookRenderer,
        temp_dir: Path,
    ):
        """Dry run should not modify target files."""
        source = temp_dir / "source.md"
        target = temp_dir / "target.md"

        source.write_text("[Link](target.md)")
        target.write_text("# Target\n\nOriginal content.")

        result = renderer.render_file(source, dry_run=True)

        target_content = target.read_text()
        assert "--- BACKLINKS ---" not in target_content
        assert result.backlinks_updated == 0

    def test_handles_relative_path_with_subdirectory(
        self,
        renderer: CodeBookRenderer,
        temp_dir: Path,
    ):
        """Should handle links to files in subdirectories."""
        subdir = temp_dir / "docs"
        subdir.mkdir()
        source = temp_dir / "source.md"
        target = subdir / "target.md"

        source.write_text("[Link](docs/target.md)")
        target.write_text("# Target")

        renderer.render_file(source)

        target_content = target.read_text()
        assert "--- BACKLINKS ---" in target_content

    def test_handles_nonexistent_target(
        self,
        renderer: CodeBookRenderer,
        temp_dir: Path,
    ):
        """Should not fail when target file doesn't exist."""
        source = temp_dir / "source.md"
        source.write_text("[Link](nonexistent.md)")

        result = renderer.render_file(source)

        assert result.success is True
        assert result.backlinks_found == 1
        assert result.backlinks_updated == 0

    def test_render_result_tracks_backlink_counts(
        self,
        renderer: CodeBookRenderer,
        temp_dir: Path,
    ):
        """Should track backlink statistics in RenderResult."""
        source = temp_dir / "source.md"
        target1 = temp_dir / "target1.md"
        target2 = temp_dir / "target2.md"

        source.write_text("[Link1](target1.md)\n[Link2](target2.md)")
        target1.write_text("# Target 1")
        target2.write_text("# Target 2")

        result = renderer.render_file(source)

        assert result.backlinks_found == 2
        assert result.backlinks_updated == 2

    def test_ignores_backlink_markers_in_code_blocks(
        self,
        renderer: CodeBookRenderer,
        temp_dir: Path,
    ):
        """Should ignore BACKLINKS markers inside fenced code blocks."""
        source = temp_dir / "source.md"
        target = temp_dir / "target.md"

        source.write_text("[Link](target.md)")
        # Target has an example BACKLINKS section in a code block
        target.write_text(
            """# Target Document

Here's an example of backlinks:

```markdown
--- BACKLINKS ---
[Example](example.md "codebook:backlink")
```

Real content below.
"""
        )

        renderer.render_file(source)

        target_content = target.read_text()
        # Should add real BACKLINKS section at the end (after the content)
        assert "Real content below." in target_content
        assert target_content.index("Real content below.") < target_content.rfind("--- BACKLINKS ---")
        # Example in code block should be preserved
        assert '```markdown\n--- BACKLINKS ---\n[Example]' in target_content
        # Real backlink should point to source
        assert 'source.md "codebook:backlink")' in target_content

    def test_ignores_backlink_markers_in_inline_code(
        self,
        renderer: CodeBookRenderer,
        temp_dir: Path,
    ):
        """Should ignore BACKLINKS markers inside inline code."""
        source = temp_dir / "source.md"
        target = temp_dir / "target.md"

        source.write_text("[Link](target.md)")
        # Target mentions the marker in inline code
        target.write_text(
            "Use `--- BACKLINKS ---` to start the backlinks section.\n"
        )

        renderer.render_file(source)

        target_content = target.read_text()
        # Should add real BACKLINKS section at the end
        assert '\n--- BACKLINKS ---\n' in target_content
        assert 'source.md "codebook:backlink")' in target_content
        # Inline code should be preserved
        assert "Use `--- BACKLINKS ---` to start" in target_content


class TestTasksDirFiltering:
    """Tests for tasks_dir filtering functionality."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create a mock CodeBook client."""
        client = MagicMock(spec=CodeBookClient)
        client.resolve_batch.return_value = {}
        return client

    def test_is_in_tasks_dir_returns_true_for_task_file(
        self,
        mock_client: MagicMock,
        temp_dir: Path,
    ):
        """Should return True for files in tasks directory."""
        from codebook.config import CodeBookConfig
        
        # Create tasks directory
        tasks_dir = temp_dir / ".codebook" / "tasks"
        tasks_dir.mkdir(parents=True)
        
        # Create a task file
        task_file = tasks_dir / "20231201-FEATURE.md"
        task_file.write_text("# Task")
        
        # Create config with tasks_dir
        config = CodeBookConfig(tasks_dir=str(tasks_dir))
        renderer = CodeBookRenderer(mock_client, config=config)
        
        assert renderer._is_in_tasks_dir(task_file) is True

    def test_is_in_tasks_dir_returns_false_for_regular_file(
        self,
        mock_client: MagicMock,
        temp_dir: Path,
    ):
        """Should return False for files outside tasks directory."""
        from codebook.config import CodeBookConfig
        
        # Create tasks directory
        tasks_dir = temp_dir / ".codebook" / "tasks"
        tasks_dir.mkdir(parents=True)
        
        # Create a regular file outside tasks
        regular_file = temp_dir / ".codebook" / "README.md"
        regular_file.write_text("# README")
        
        # Create config with tasks_dir
        config = CodeBookConfig(tasks_dir=str(tasks_dir))
        renderer = CodeBookRenderer(mock_client, config=config)
        
        assert renderer._is_in_tasks_dir(regular_file) is False

    def test_render_directory_excludes_tasks_dir(
        self,
        mock_client: MagicMock,
        temp_dir: Path,
    ):
        """Should exclude files in tasks_dir when rendering directory."""
        from codebook.config import CodeBookConfig
        
        # Create directory structure
        codebook_dir = temp_dir / ".codebook"
        codebook_dir.mkdir()
        tasks_dir = codebook_dir / "tasks"
        tasks_dir.mkdir()
        
        # Create regular files
        (codebook_dir / "README.md").write_text("# README")
        (codebook_dir / "GUIDE.md").write_text("# Guide")
        
        # Create task files
        (tasks_dir / "20231201-FEATURE.md").write_text("# Task 1")
        (tasks_dir / "20231202-BUGFIX.md").write_text("# Task 2")
        
        # Create config
        config = CodeBookConfig(tasks_dir=str(tasks_dir))
        renderer = CodeBookRenderer(mock_client, config=config)
        
        # Render directory
        results = renderer.render_directory(codebook_dir, recursive=True)
        
        # Should only process regular files, not task files
        assert len(results) == 2
        processed_files = {r.path.name for r in results}
        assert processed_files == {"README.md", "GUIDE.md"}

    def test_render_directory_with_nested_tasks_dir(
        self,
        mock_client: MagicMock,
        temp_dir: Path,
    ):
        """Should exclude nested tasks_dir files."""
        from codebook.config import CodeBookConfig
        
        # Create nested structure
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()
        tasks_dir = temp_dir / "tasks"
        tasks_dir.mkdir()
        
        # Create files
        (docs_dir / "api.md").write_text("# API")
        (tasks_dir / "task.md").write_text("# Task")
        (temp_dir / "README.md").write_text("# README")
        
        # Create config
        config = CodeBookConfig(tasks_dir=str(tasks_dir))
        renderer = CodeBookRenderer(mock_client, config=config)
        
        # Render from root
        results = renderer.render_directory(temp_dir, recursive=True)
        
        # Should exclude task file
        assert len(results) == 2
        processed_files = {r.path.name for r in results}
        assert processed_files == {"api.md", "README.md"}
