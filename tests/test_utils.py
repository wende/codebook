"""Tests for CodeBook utility functions."""

from pathlib import Path

import pytest

from codebook.parser import CodeBookLink, LinkType
from codebook.utils import CodeBookStatusChecker, LinkValidationResult, StatusReport


class TestStatusReport:
    """Test StatusReport dataclass."""

    def test_no_issues(self):
        """Test report with no issues."""
        report = StatusReport()
        assert not report.has_warnings
        assert not report.has_errors
        assert report.exit_code == 0

    def test_with_warnings(self):
        """Test report with warnings."""
        report = StatusReport(
            broken_file_links=[
                LinkValidationResult(
                    link=CodeBookLink("", "", "", 0, 0),
                    file_path=Path("test.md"),
                    line_number=1,
                    is_valid=False,
                    error_message="File not found",
                )
            ]
        )
        assert report.has_warnings
        assert not report.has_errors
        assert report.exit_code == 1

    def test_with_errors(self):
        """Test report with critical errors."""
        report = StatusReport(
            backend_url="http://localhost:3000",
            backend_healthy=False,
            backend_check_requested=True,  # Must request check for it to be an error
        )
        assert not report.has_warnings
        assert report.has_errors
        assert report.exit_code == 2

    def test_errors_take_precedence(self):
        """Test that errors take precedence over warnings."""
        report = StatusReport(
            backend_url="http://localhost:3000",
            backend_healthy=False,
            backend_check_requested=True,  # Must request check for it to be an error
            broken_file_links=[
                LinkValidationResult(
                    link=CodeBookLink("", "", "", 0, 0),
                    file_path=Path("test.md"),
                    line_number=1,
                    is_valid=False,
                )
            ],
        )
        assert report.has_warnings
        assert report.has_errors
        assert report.exit_code == 2


class TestCodeBookStatusChecker:
    """Test CodeBookStatusChecker."""

    @pytest.fixture
    def checker(self, tmp_path):
        """Create a status checker."""
        return CodeBookStatusChecker(tmp_path)

    def test_get_task_statistics_empty(self, checker, tmp_path):
        """Test task statistics with no tasks."""
        tasks_dir = tmp_path / "tasks"
        total, recent = checker.get_task_statistics(tasks_dir)
        assert total == 0
        assert recent == []

    def test_get_task_statistics(self, checker, tmp_path):
        """Test task statistics with tasks."""
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()

        # Create some task files
        (tasks_dir / "task1.md").write_text("Task 1")
        (tasks_dir / "task2.md").write_text("Task 2")
        (tasks_dir / "task3.md").write_text("Task 3")

        total, recent = checker.get_task_statistics(tasks_dir)
        assert total == 3
        assert len(recent) == 3

    def test_validate_file_link_exists(self, checker, tmp_path):
        """Test validating a link to an existing file."""
        # Create target file
        target = tmp_path / "target.md"
        target.write_text("# Target")

        # Create source file
        source = tmp_path / "source.md"
        source.write_text("[link](target.md)")

        link = CodeBookLink(
            full_match="[link](target.md)",
            value="target.md",
            template="",
            start=0,
            end=17,
            link_type=LinkType.MARKDOWN_LINK,
            extra="link",
        )

        result = checker.validate_file_link(link, source, 1)
        assert result.is_valid
        assert result.error_message is None

    def test_validate_file_link_missing(self, checker, tmp_path):
        """Test validating a link to a missing file."""
        source = tmp_path / "source.md"
        source.write_text("[link](missing.md)")

        link = CodeBookLink(
            full_match="[link](missing.md)",
            value="missing.md",
            template="",
            start=0,
            end=18,
            link_type=LinkType.MARKDOWN_LINK,
            extra="link",
        )

        result = checker.validate_file_link(link, source, 1)
        assert not result.is_valid
        assert "File not found" in result.error_message

    def test_validate_file_link_with_section(self, checker, tmp_path):
        """Test validating a link with section anchor."""
        # Create target file with heading
        target = tmp_path / "target.md"
        target.write_text("# My Heading\n\nContent here.")

        # Create source file
        source = tmp_path / "source.md"
        source.write_text("[link](target.md#my-heading)")

        link = CodeBookLink(
            full_match="[link](target.md#my-heading)",
            value="target.md#my-heading",
            template="",
            start=0,
            end=28,
            link_type=LinkType.MARKDOWN_LINK,
            extra="link",
        )

        result = checker.validate_file_link(link, source, 1)
        assert result.is_valid
        assert result.error_message is None

    def test_validate_file_link_with_missing_section(self, checker, tmp_path):
        """Test validating a link with missing section anchor."""
        # Create target file without the heading
        target = tmp_path / "target.md"
        target.write_text("# Different Heading\n\nContent here.")

        # Create source file
        source = tmp_path / "source.md"
        source.write_text("[link](target.md#my-heading)")

        link = CodeBookLink(
            full_match="[link](target.md#my-heading)",
            value="target.md#my-heading",
            template="",
            start=0,
            end=28,
            link_type=LinkType.MARKDOWN_LINK,
            extra="link",
        )

        result = checker.validate_file_link(link, source, 1)
        assert not result.is_valid
        assert "Section not found" in result.error_message

    def test_validate_exec_block_valid(self, checker, tmp_path):
        """Test validating a valid Python EXEC block."""
        source = tmp_path / "source.md"
        link = CodeBookLink(
            full_match="",
            value="",
            template='print("hello")',
            start=0,
            end=0,
            link_type=LinkType.EXEC,
            extra="python",
        )

        result = checker.validate_exec_block(link, source, 1)
        assert result.is_valid

    def test_validate_exec_block_syntax_error(self, checker, tmp_path):
        """Test validating an EXEC block with syntax error."""
        source = tmp_path / "source.md"
        link = CodeBookLink(
            full_match="",
            value="",
            template="print('unclosed",
            start=0,
            end=0,
            link_type=LinkType.EXEC,
            extra="python",
        )

        result = checker.validate_exec_block(link, source, 1)
        assert not result.is_valid
        assert "syntax error" in result.error_message.lower()

    def test_validate_exec_block_unsupported_language(self, checker, tmp_path):
        """Test validating an EXEC block with unsupported language."""
        source = tmp_path / "source.md"
        link = CodeBookLink(
            full_match="",
            value="",
            template="console.log('hello')",
            start=0,
            end=0,
            link_type=LinkType.EXEC,
            extra="javascript",
        )

        result = checker.validate_exec_block(link, source, 1)
        assert not result.is_valid
        assert "Unsupported language" in result.error_message

    def test_validate_cicada_block_valid(self, checker, tmp_path):
        """Test validating a valid CICADA block."""
        source = tmp_path / "source.md"
        link = CodeBookLink(
            full_match="",
            value="",
            template="query",
            start=0,
            end=0,
            link_type=LinkType.CICADA,
            params={"query": "authentication"},
        )

        result = checker.validate_cicada_block(link, source, 1)
        assert result.is_valid

    def test_validate_cicada_block_invalid_endpoint(self, checker, tmp_path):
        """Test validating a CICADA block with invalid endpoint."""
        source = tmp_path / "source.md"
        link = CodeBookLink(
            full_match="",
            value="",
            template="invalid-endpoint",
            start=0,
            end=0,
            link_type=LinkType.CICADA,
            params={},
        )

        result = checker.validate_cicada_block(link, source, 1)
        assert not result.is_valid
        assert "Invalid endpoint" in result.error_message

    def test_validate_cicada_block_missing_param(self, checker, tmp_path):
        """Test validating a CICADA block with missing required param."""
        source = tmp_path / "source.md"
        link = CodeBookLink(
            full_match="",
            value="",
            template="query",
            start=0,
            end=0,
            link_type=LinkType.CICADA,
            params={},  # Missing 'query' param
        )

        result = checker.validate_cicada_block(link, source, 1)
        assert not result.is_valid
        assert "Missing required parameter" in result.error_message

    def test_validate_cicada_search_module_with_module_name(self, checker, tmp_path):
        """Test search-module with module_name parameter."""
        source = tmp_path / "source.md"
        link = CodeBookLink(
            full_match="",
            value="",
            template="search-module",
            start=0,
            end=0,
            link_type=LinkType.CICADA,
            params={"module_name": "MyApp.User"},
        )

        result = checker.validate_cicada_block(link, source, 1)
        assert result.is_valid

    def test_validate_cicada_search_module_with_file_path(self, checker, tmp_path):
        """Test search-module with file_path parameter."""
        source = tmp_path / "source.md"
        link = CodeBookLink(
            full_match="",
            value="",
            template="search-module",
            start=0,
            end=0,
            link_type=LinkType.CICADA,
            params={"file_path": "lib/my_app/user.ex"},
        )

        result = checker.validate_cicada_block(link, source, 1)
        assert result.is_valid

    def test_validate_cicada_search_module_without_params(self, checker, tmp_path):
        """Test search-module without required parameters."""
        source = tmp_path / "source.md"
        link = CodeBookLink(
            full_match="",
            value="",
            template="search-module",
            start=0,
            end=0,
            link_type=LinkType.CICADA,
            params={},  # Missing both module_name and file_path
        )

        result = checker.validate_cicada_block(link, source, 1)
        assert not result.is_valid
        assert "either module_name or file_path" in result.error_message

    def test_scan_file(self, checker, tmp_path):
        """Test scanning a file for link issues."""
        # Create a markdown file with various links
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """
# Test File

[Good link](test.md)
[Bad link](missing.md)

<exec lang="python">
print("valid")
</exec>
<output></output>

<exec lang="python">
print('syntax error
</exec>
<output></output>

<cicada endpoint="query" query="test">
</cicada>

<cicada endpoint="invalid">
</cicada>
"""
        )

        results = list(checker.scan_file(md_file))

        # Should find: 1 broken link, 1 syntax error, 1 invalid endpoint
        invalid_results = [r for r in results if not r.is_valid]
        assert len(invalid_results) == 3
