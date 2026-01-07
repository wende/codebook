"""Utility functions for CodeBook status and health checks.

This module provides validation and health checking for CodeBook documentation:
- Task statistics
- Link validation (file references, section anchors)
- EXEC block syntax validation
- CICADA block validation
- Backend/Cicada connectivity checks
"""

import ast
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from .parser import CodeBookLink, CodeBookParser, LinkType


@dataclass
class LinkValidationResult:
    """Result of validating a single link."""

    link: CodeBookLink
    file_path: Path
    line_number: int
    is_valid: bool
    error_message: str | None = None


@dataclass
class StatusReport:
    """Complete status report for CodeBook environment."""

    # Task statistics
    total_tasks: int = 0
    recent_tasks: list[Path] = field(default_factory=list)

    # Link health
    total_links: int = 0
    broken_file_links: list[LinkValidationResult] = field(default_factory=list)
    broken_section_links: list[LinkValidationResult] = field(default_factory=list)
    invalid_exec_blocks: list[LinkValidationResult] = field(default_factory=list)
    invalid_cicada_blocks: list[LinkValidationResult] = field(default_factory=list)

    # Backend connectivity
    backend_url: str | None = None
    backend_healthy: bool = False
    backend_response_time: float | None = None
    backend_error: str | None = None
    backend_check_requested: bool = False

    # Cicada connectivity
    cicada_url: str | None = None
    cicada_healthy: bool = False
    cicada_error: str | None = None
    cicada_check_requested: bool = False

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return bool(
            self.broken_file_links
            or self.broken_section_links
            or self.invalid_exec_blocks
            or self.invalid_cicada_blocks
        )

    @property
    def has_errors(self) -> bool:
        """Check if there are critical errors.

        Only considers backend/cicada errors if checks were explicitly requested.
        """
        backend_error = (
            self.backend_check_requested and self.backend_url and not self.backend_healthy
        )
        cicada_error = self.cicada_check_requested and self.cicada_url and not self.cicada_healthy
        return bool(backend_error or cicada_error)

    @property
    def exit_code(self) -> int:
        """Get appropriate exit code based on status."""
        if self.has_errors:
            return 2
        elif self.has_warnings:
            return 1
        return 0


class CodeBookStatusChecker:
    """Health checker for CodeBook documentation."""

    # Valid Cicada endpoints
    VALID_CICADA_ENDPOINTS = {
        "query",
        "search-function",
        "search-module",
        "git-history",
        "expand-result",
        "refresh-index",
        "query-jq",
    }

    # Required parameters for each Cicada endpoint
    CICADA_REQUIRED_PARAMS = {
        "query": ["query"],
        "search-function": ["function_name"],
        "search-module": [],  # module_name or file_path (at least one)
        "git-history": ["file_path"],
        "expand-result": ["identifier"],
        "refresh-index": [],
        "query-jq": ["query"],
    }

    def __init__(self, base_dir: Path):
        """Initialize status checker.

        Args:
            base_dir: Base directory containing CodeBook documentation
        """
        self.base_dir = base_dir
        self.parser = CodeBookParser()

    def get_task_statistics(self, tasks_dir: Path) -> tuple[int, list[Path]]:
        """Get task statistics.

        Args:
            tasks_dir: Directory containing tasks

        Returns:
            Tuple of (total_count, recent_tasks)
        """
        if not tasks_dir.exists():
            return 0, []

        task_files = sorted(tasks_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        return len(task_files), task_files[:5]  # Return 5 most recent

    def validate_file_link(
        self, link: CodeBookLink, source_file: Path, line_number: int
    ) -> LinkValidationResult:
        """Validate a file reference link.

        Args:
            link: The link to validate
            source_file: Source file containing the link
            line_number: Line number of the link

        Returns:
            Validation result
        """
        # Parse file path and section anchor
        target = link.value
        if "#" in target:
            file_part, section = target.split("#", 1)
        else:
            file_part, section = target, None

        # Resolve relative path from source file
        target_path = (source_file.parent / file_part).resolve()

        # Check if file exists
        if not target_path.exists():
            return LinkValidationResult(
                link=link,
                file_path=source_file,
                line_number=line_number,
                is_valid=False,
                error_message=f"File not found: {file_part}",
            )

        # If section anchor specified, validate it exists
        if section:
            if not self._validate_section_anchor(target_path, section):
                return LinkValidationResult(
                    link=link,
                    file_path=source_file,
                    line_number=line_number,
                    is_valid=False,
                    error_message=f"Section not found: #{section}",
                )

        return LinkValidationResult(
            link=link,
            file_path=source_file,
            line_number=line_number,
            is_valid=True,
        )

    def _validate_section_anchor(self, file_path: Path, anchor: str) -> bool:
        """Validate that a section anchor exists in a markdown file.

        Args:
            file_path: Path to markdown file
            anchor: Section anchor (without #)

        Returns:
            True if anchor exists
        """
        try:
            content = file_path.read_text()
        except (FileNotFoundError, PermissionError, UnicodeDecodeError, OSError):
            return False

        # Normalize the expected anchor using GitHub slug rules
        # Same normalization as applied to headings
        expected_slug = anchor.lower()
        expected_slug = re.sub(r"[^\w\s-]", "", expected_slug)  # Remove special chars
        expected_slug = re.sub(r"[-\s]+", "-", expected_slug)  # Collapse spaces/dashes
        expected_slug = expected_slug.strip("-")

        # Find all headings in the file
        heading_pattern = re.compile(r"^#+\s+(.+)$", re.MULTILINE)
        for match in heading_pattern.finditer(content):
            heading_text = match.group(1)
            # Convert heading to slug with same rules
            slug = heading_text.lower()
            slug = re.sub(r"[^\w\s-]", "", slug)
            slug = re.sub(r"[-\s]+", "-", slug)
            slug = slug.strip("-")

            if slug == expected_slug:
                return True

        return False

    def validate_exec_block(
        self, link: CodeBookLink, source_file: Path, line_number: int
    ) -> LinkValidationResult:
        """Validate an EXEC block.

        Args:
            link: The exec block link
            source_file: Source file containing the block
            line_number: Line number of the block

        Returns:
            Validation result
        """
        # Check language is supported
        language = link.extra  # language is stored in extra field
        if language != "python":
            return LinkValidationResult(
                link=link,
                file_path=source_file,
                line_number=line_number,
                is_valid=False,
                error_message=f"Unsupported language: {language} (only 'python' supported)",
            )

        # Validate Python syntax
        code = link.template  # code is stored in template field
        try:
            ast.parse(code)
        except SyntaxError as e:
            return LinkValidationResult(
                link=link,
                file_path=source_file,
                line_number=line_number,
                is_valid=False,
                error_message=f"Python syntax error: {e.msg} (line {e.lineno})",
            )

        return LinkValidationResult(
            link=link,
            file_path=source_file,
            line_number=line_number,
            is_valid=True,
        )

    def validate_cicada_block(
        self, link: CodeBookLink, source_file: Path, line_number: int
    ) -> LinkValidationResult:
        """Validate a CICADA block.

        Args:
            link: The cicada block link
            source_file: Source file containing the block
            line_number: Line number of the block

        Returns:
            Validation result

        Note:
            The search-module endpoint accepts either module_name OR file_path,
            not both required. Other endpoints follow standard param requirements
            defined in CICADA_REQUIRED_PARAMS.
        """
        endpoint = link.template  # endpoint is stored in template field
        params = link.params  # parameters dict

        # Validate endpoint
        if endpoint not in self.VALID_CICADA_ENDPOINTS:
            valid_list = ", ".join(sorted(self.VALID_CICADA_ENDPOINTS))
            return LinkValidationResult(
                link=link,
                file_path=source_file,
                line_number=line_number,
                is_valid=False,
                error_message=f"Invalid endpoint: {endpoint} (valid: {valid_list})",
            )

        # Special case: search-module accepts either module_name OR file_path (at least one)
        if endpoint == "search-module":
            if "module_name" not in params and "file_path" not in params:
                return LinkValidationResult(
                    link=link,
                    file_path=source_file,
                    line_number=line_number,
                    is_valid=False,
                    error_message="search-module requires either module_name or file_path parameter",
                )
            # Validation passed for search-module
            return LinkValidationResult(
                link=link,
                file_path=source_file,
                line_number=line_number,
                is_valid=True,
            )

        # Standard validation: check all required parameters are present
        required = self.CICADA_REQUIRED_PARAMS.get(endpoint, [])
        for param in required:
            if param not in params:
                return LinkValidationResult(
                    link=link,
                    file_path=source_file,
                    line_number=line_number,
                    is_valid=False,
                    error_message=f"Missing required parameter: {param}",
                )

        # All validations passed
        return LinkValidationResult(
            link=link,
            file_path=source_file,
            line_number=line_number,
            is_valid=True,
        )

    def _get_line_number(self, content: str, position: int) -> int:
        """Get line number for a character position.

        Args:
            content: File content
            position: Character position

        Returns:
            Line number (1-indexed)
        """
        return content[:position].count("\n") + 1

    def scan_file(self, file_path: Path) -> Iterator[LinkValidationResult]:
        """Scan a markdown file for link issues.

        Args:
            file_path: Path to markdown file

        Yields:
            Validation results for each link
        """
        try:
            content = file_path.read_text()
        except (FileNotFoundError, PermissionError, UnicodeDecodeError, OSError):
            # Skip files that can't be read (expected errors only)
            return

        for link in self.parser.find_links(content):
            line_number = self._get_line_number(content, link.start)

            # Validate based on link type
            if link.link_type == LinkType.MARKDOWN_LINK:
                # Skip external URLs
                if link.value.startswith(("http://", "https://", "mailto:")):
                    continue
                yield self.validate_file_link(link, file_path, line_number)

            elif link.link_type == LinkType.EXEC:
                yield self.validate_exec_block(link, file_path, line_number)

            elif link.link_type == LinkType.CICADA:
                yield self.validate_cicada_block(link, file_path, line_number)

    def scan_directory(self, directory: Path) -> list[LinkValidationResult]:
        """Scan all markdown files in a directory.

        Args:
            directory: Directory to scan

        Returns:
            List of all validation results
        """
        results = []
        for md_file in directory.rglob("*.md"):
            results.extend(self.scan_file(md_file))
        return results
