"""File renderer for CodeBook markdown files.

This module handles reading markdown files, resolving codebook links
via the HTTP client, and writing the updated content back.

Also supports executing code blocks via Jupyter kernels and
Cicada API queries for code exploration.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .parser import CodeBookParser, Frontmatter, LinkType
from .client import CodeBookClient


def get_codebook_version() -> str:
    """Get the current codebook version from git.

    Returns:
        Version string in format 'tag (short_sha)' or just 'sha' if no tag.
    """
    try:
        # Get the short commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )
        if result.returncode != 0:
            return "dev"

        sha = result.stdout.strip()
        if not sha:
            return "dev"

        # Try to get a tag pointing to this commit
        tag_result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match", "HEAD"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )
        tag = tag_result.stdout.strip() if tag_result.returncode == 0 else ""

        if tag:
            return f"{tag} ({sha})"
        return sha
    except Exception:
        return "dev"

if TYPE_CHECKING:
    from .kernel import CodeBookKernel
    from .cicada import CicadaClient

from .cicada import jq_query, format_json_value

logger = logging.getLogger(__name__)


@dataclass
class RenderResult:
    """Result of rendering a file.

    Attributes:
        path: Path to the rendered file
        templates_found: Number of codebook links found
        templates_resolved: Number of templates successfully resolved
        code_blocks_found: Number of executable code blocks found
        code_blocks_executed: Number of code blocks successfully executed
        cicada_queries_found: Number of Cicada query blocks found
        cicada_queries_executed: Number of Cicada queries executed
        backlinks_found: Number of bidirectional links found
        backlinks_updated: Number of target files updated with backlinks
        changed: Whether the file content was modified
        error: Error message if rendering failed, None otherwise
        frontmatter: Parsed frontmatter from the file
    """

    path: Path
    templates_found: int = 0
    templates_resolved: int = 0
    code_blocks_found: int = 0
    code_blocks_executed: int = 0
    cicada_queries_found: int = 0
    cicada_queries_executed: int = 0
    backlinks_found: int = 0
    backlinks_updated: int = 0
    changed: bool = False
    error: str | None = None
    frontmatter: Frontmatter | None = None

    @property
    def success(self) -> bool:
        """Whether rendering completed without errors."""
        return self.error is None


class CodeBookRenderer:
    """Renderer for updating codebook links in markdown files.

    The renderer reads markdown files, extracts codebook links,
    resolves their templates via HTTP, and updates the files in-place.

    Also supports executing code blocks via Jupyter kernels and
    Cicada API queries for code exploration.

    Example:
        >>> client = CodeBookClient(base_url="http://localhost:3000")
        >>> renderer = CodeBookRenderer(client)
        >>> result = renderer.render_file(Path("docs/readme.md"))
        >>> print(f"Updated {result.templates_resolved} templates")
    """

    def __init__(
        self,
        client: CodeBookClient,
        kernel: CodeBookKernel | None = None,
        cicada: CicadaClient | None = None,
    ):
        """Initialize the renderer.

        Args:
            client: HTTP client for resolving templates
            kernel: Optional Jupyter kernel for executing code blocks
            cicada: Optional Cicada client for code exploration queries
        """
        self.client = client
        self.kernel = kernel
        self.cicada = cicada
        self.parser = CodeBookParser()

    def render_file(self, path: Path, dry_run: bool = False) -> RenderResult:
        """Render a single markdown file.

        Args:
            path: Path to the markdown file
            dry_run: If True, don't write changes back to file

        Returns:
            RenderResult with details about the operation
        """
        result = RenderResult(path=path)

        try:
            content = path.read_text(encoding="utf-8")
        except OSError as e:
            result.error = f"Failed to read file: {e}"
            return result

        # Parse frontmatter
        frontmatter, content_body = self.parser.parse_frontmatter(content)
        result.frontmatter = frontmatter

        # Check if links are disabled via frontmatter
        if frontmatter.links_disabled:
            logger.debug(f"Links disabled via frontmatter in {path}")
            return result

        # Find all links
        all_links = list(self.parser.find_links(content))

        # Separate different link types
        exec_blocks = [link for link in all_links if link.link_type == LinkType.EXEC]
        cicada_blocks = [link for link in all_links if link.link_type == LinkType.CICADA]
        markdown_links = [
            link for link in all_links if link.link_type == LinkType.MARKDOWN_LINK
        ]
        template_links = [
            link for link in all_links
            if link.link_type not in (
                LinkType.EXEC, LinkType.CICADA, LinkType.MARKDOWN_LINK, LinkType.BACKLINK
            )
        ]

        # Count templates (excluding exec, cicada, bidirectional, and backlink blocks)
        templates = list({link.template for link in template_links})
        result.templates_found = len(templates)
        result.code_blocks_found = len(exec_blocks)
        result.cicada_queries_found = len(cicada_blocks)
        result.backlinks_found = len(markdown_links)

        new_content = content

        # Resolve templates
        if templates:
            values: dict[str, str] = {}

            # Handle special local templates
            local_templates = [t for t in templates if t.startswith("codebook.")]
            remote_templates = [t for t in templates if not t.startswith("codebook.")]

            for template in local_templates:
                if template == "codebook.version":
                    values[template] = get_codebook_version()

            # Resolve remaining templates via HTTP
            if remote_templates:
                remote_values = self.client.resolve_batch(remote_templates)
                values.update(remote_values)

            result.templates_resolved = len(values)

            if values:
                new_content = self.parser.replace_values(new_content, values)

        # Execute code blocks via kernel
        if exec_blocks and self.kernel:
            new_content, executed = self._execute_code_blocks(new_content, exec_blocks)
            result.code_blocks_executed = executed

        # Execute Cicada queries
        if cicada_blocks and self.cicada:
            new_content, executed = self._execute_cicada_queries(new_content, cicada_blocks)
            result.cicada_queries_executed = executed

        # Update backlinks in target files for markdown links (unless disabled)
        if markdown_links and not dry_run and not frontmatter.backlinks_disabled:
            updated = self._update_backlinks(path, markdown_links)
            result.backlinks_updated = updated

        result.changed = new_content != content

        if result.changed and not dry_run:
            try:
                path.write_text(new_content, encoding="utf-8")
                logger.info(
                    f"Updated {path}: {result.templates_resolved}/{result.templates_found} templates, "
                    f"{result.code_blocks_executed}/{result.code_blocks_found} code blocks, "
                    f"{result.cicada_queries_executed}/{result.cicada_queries_found} cicada queries"
                )
            except OSError as e:
                result.error = f"Failed to write file: {e}"
                return result

        return result

    def _execute_code_blocks(
        self, content: str, exec_blocks: list
    ) -> tuple[str, int]:
        """Execute code blocks and update content with results.

        Args:
            content: The markdown content
            exec_blocks: List of CodeBookLink objects for exec blocks

        Returns:
            Tuple of (updated content, number of blocks executed)
        """
        executed = 0

        for block in exec_blocks:
            code = block.template  # code is stored in template field
            lang = block.extra  # language is stored in extra field

            # Only execute Python for now
            if lang != "python":
                logger.warning(f"Unsupported language for execution: {lang}")
                continue

            try:
                result = self.kernel.execute(code)
                if result.success:
                    # Replace the exec block with updated output
                    new_block = f'<exec lang="{lang}">\n{code}\n</exec>\n<output>\n{result.output}\n</output>'
                    content = content.replace(block.full_match, new_block)
                    executed += 1
                else:
                    # Include error in output
                    error_output = f"Error: {result.error}"
                    new_block = f'<exec lang="{lang}">\n{code}\n</exec>\n<output>\n{error_output}\n</output>'
                    content = content.replace(block.full_match, new_block)
                    logger.error(f"Code execution failed: {result.error}")
            except Exception as e:
                logger.error(f"Failed to execute code block: {e}")

        return content, executed

    def _execute_cicada_queries(
        self, content: str, cicada_blocks: list
    ) -> tuple[str, int]:
        """Execute Cicada queries and update content with results.

        Args:
            content: The markdown content
            cicada_blocks: List of CodeBookLink objects for cicada blocks

        Returns:
            Tuple of (updated content, number of queries executed)
        """
        executed = 0

        for block in cicada_blocks:
            endpoint = block.template
            params = block.params

            try:
                # Get format parameter (passed to all endpoints)
                fmt = params.get("format")

                # Call the appropriate Cicada endpoint
                if endpoint == "query":
                    keywords = params.get("keywords", "").split(",") if params.get("keywords") else None
                    result = self.cicada.query(
                        keywords=[k.strip() for k in keywords] if keywords else None,
                        pattern=params.get("pattern"),
                        scope=params.get("scope", "all"),
                        filter_type=params.get("filter_type", "all"),
                        show_snippets=params.get("show_snippets", "false").lower() == "true",
                        format=fmt,
                    )
                elif endpoint == "search-function":
                    result = self.cicada.search_function(
                        function_name=params.get("function_name", ""),
                        module_name=params.get("module_name"),
                        format=fmt,
                    )
                elif endpoint == "search-module":
                    result = self.cicada.search_module(
                        module_name=params.get("module_name"),
                        file_path=params.get("file_path"),
                        format=fmt,
                    )
                elif endpoint == "git-history":
                    result = self.cicada.git_history(
                        file_path=params.get("file_path"),
                        module_name=params.get("module_name"),
                        limit=int(params.get("limit", "10")),
                        format=fmt,
                    )
                else:
                    logger.warning(f"Unknown Cicada endpoint: {endpoint}")
                    continue

                if result.success:
                    # Check if jq extraction is requested
                    jq_path = params.get("jq")
                    if jq_path and result.raw_data is not None:
                        # Apply jq query extraction
                        extracted = jq_query(result.raw_data, jq_path)
                        output_content = format_json_value(extracted)
                    else:
                        output_content = result.content

                    # Wrap in code fence if render="code" or render="code[lang]"
                    render_mode = params.get("render", "")
                    if render_mode.startswith("code"):
                        # Parse lang from "code[json]" format or fall back to lang param
                        lang = ""
                        if "[" in render_mode and render_mode.endswith("]"):
                            lang = render_mode[render_mode.index("[") + 1 : -1]
                        else:
                            lang = params.get("lang", "")
                        output_content = f"\n```{lang}\n{output_content}\n```"

                    # Build the new block with updated content
                    attrs = f'endpoint="{endpoint}"'
                    for key, val in params.items():
                        attrs += f' {key}="{val}"'
                    new_block = f"<cicada {attrs}>\n{output_content}\n</cicada>"
                    content = content.replace(block.full_match, new_block)
                    executed += 1
                else:
                    error_content = f"Error: {result.error}"
                    attrs = f'endpoint="{endpoint}"'
                    for key, val in params.items():
                        attrs += f' {key}="{val}"'
                    new_block = f"<cicada {attrs}>\n{error_content}\n</cicada>"
                    content = content.replace(block.full_match, new_block)
                    logger.error(f"Cicada query failed: {result.error}")
            except Exception as e:
                logger.error(f"Failed to execute Cicada query: {e}")
                # Write error to block
                error_content = f"Error: {e}"
                attrs = f'endpoint="{endpoint}"'
                for key, val in params.items():
                    attrs += f' {key}="{val}"'
                new_block = f"<cicada {attrs}>\n{error_content}\n</cicada>"
                content = content.replace(block.full_match, new_block)

        return content, executed

    def _find_real_backlinks_section(self, content: str) -> int | None:
        """Find the position of the real BACKLINKS section, ignoring examples.

        The BACKLINKS section should be at the end of the file, after any
        content sections. This avoids false positives from example backlinks
        in code blocks or inline code.

        Args:
            content: Markdown content to search

        Returns:
            Position of the BACKLINKS marker, or None if not found
        """
        import re
        backlinks_marker = "--- BACKLINKS ---"

        # Find all fenced code block ranges (``` or ~~~)
        code_block_ranges = []
        for match in re.finditer(r'(```|~~~)[^\n]*\n.*?\1', content, flags=re.DOTALL):
            code_block_ranges.append((match.start(), match.end()))

        def is_in_code_block(pos: int) -> bool:
            """Check if a position is inside a fenced code block."""
            return any(start <= pos < end for start, end in code_block_ranges)

        # Look for the marker on its own line
        pattern = re.compile(r'^[ \t]*' + re.escape(backlinks_marker) + r'[ \t]*$', re.MULTILINE)

        # Find the last match that is NOT inside a code block
        for match in reversed(list(pattern.finditer(content))):
            if not is_in_code_block(match.start()):
                return match.start()

        return None

    def _update_backlinks(
        self, source_path: Path, markdown_links: list
    ) -> int:
        """Update backlinks in target files for markdown links.

        For each markdown link [text](file.md) pointing to a .md file, this method:
        1. Resolves the target file path from the URL
        2. Adds or updates a backlink in the target file's BACKLINKS section

        Args:
            source_path: Path to the source file containing markdown links
            markdown_links: List of CodeBookLink objects for markdown links

        Returns:
            Number of target files successfully updated
        """
        updated = 0
        backlinks_marker = "--- BACKLINKS ---"

        for link in markdown_links:
            target_url = link.value  # URL to the target file
            link_text = link.extra  # Text to display in the backlink

            # Resolve target path relative to source file's directory
            if target_url.startswith("/"):
                # Absolute path from project root - find git root
                try:
                    import subprocess
                    result = subprocess.run(
                        ["git", "rev-parse", "--show-toplevel"],
                        capture_output=True,
                        text=True,
                        cwd=source_path.parent,
                    )
                    if result.returncode == 0:
                        git_root = Path(result.stdout.strip())
                        target_path = git_root / target_url.lstrip("/")
                    else:
                        target_path = source_path.parent / target_url.lstrip("/")
                except Exception:
                    target_path = source_path.parent / target_url.lstrip("/")
            else:
                # Relative path
                target_path = (source_path.parent / target_url).resolve()

            if not target_path.exists():
                logger.warning(f"Target file not found for backlink: {target_path}")
                continue

            try:
                target_content = target_path.read_text(encoding="utf-8")
            except OSError as e:
                logger.error(f"Failed to read target file {target_path}: {e}")
                continue

            # Calculate relative path from target back to source
            try:
                backlink_url = source_path.relative_to(target_path.parent)
            except ValueError:
                # Files are not in a parent/child relationship, use relative path
                try:
                    # Try to find common base
                    backlink_url = Path(
                        "../" * len(target_path.parent.parts)
                    ) / source_path
                    # Simplify the path
                    import os
                    backlink_url = Path(
                        os.path.relpath(source_path, target_path.parent)
                    )
                except Exception:
                    backlink_url = source_path

            # Create the backlink entry
            backlink_entry = f'[{link_text}]({backlink_url} "codebook:backlink")'

            # Find the real BACKLINKS section (on its own line, not in examples)
            marker_pos = self._find_real_backlinks_section(target_content)

            if marker_pos is not None:
                section_start = marker_pos + len(backlinks_marker)

                # Get existing backlinks section
                existing_section = target_content[section_start:]

                # Check if a backlink from this source already exists
                # Look for any backlink pointing to our source file
                source_name = source_path.name
                if f'({backlink_url} "codebook:backlink")' in existing_section:
                    # Backlink already exists, skip
                    continue
                elif f'{source_name} "codebook:backlink")' in existing_section:
                    # Backlink to same file exists (possibly different path), skip
                    continue

                # Add new backlink after the marker
                new_content = (
                    target_content[:section_start]
                    + "\n"
                    + backlink_entry
                    + target_content[section_start:]
                )
            else:
                # Add BACKLINKS section at the end of the file
                new_content = (
                    target_content.rstrip()
                    + "\n\n"
                    + backlinks_marker
                    + "\n"
                    + backlink_entry
                    + "\n"
                )

            # Write updated content
            try:
                target_path.write_text(new_content, encoding="utf-8")
                logger.info(f"Added backlink to {target_path} from {source_path}")
                updated += 1
            except OSError as e:
                logger.error(f"Failed to write backlink to {target_path}: {e}")

        return updated

    def render_directory(
        self,
        directory: Path,
        recursive: bool = True,
        dry_run: bool = False,
    ) -> list[RenderResult]:
        """Render all markdown files in a directory.

        Args:
            directory: Path to the directory
            recursive: If True, process subdirectories recursively
            dry_run: If True, don't write changes back to files

        Returns:
            List of RenderResult objects, one per file processed
        """
        if not directory.is_dir():
            return [
                RenderResult(
                    path=directory,
                    error=f"Not a directory: {directory}",
                )
            ]

        results: list[RenderResult] = []
        pattern = "**/*.md" if recursive else "*.md"

        for md_file in sorted(directory.glob(pattern)):
            if md_file.is_file():
                result = self.render_file(md_file, dry_run=dry_run)
                results.append(result)

        return results

    def render_content(self, content: str) -> tuple[str, dict[str, str]]:
        """Render markdown content without file I/O.

        Useful for generating diffs or previews.

        Args:
            content: Markdown content to render

        Returns:
            Tuple of (rendered content, resolved values dict)
        """
        templates = self.parser.find_templates(content)

        if not templates:
            return content, {}

        values = self.client.resolve_batch(templates)

        if not values:
            return content, {}

        new_content = self.parser.replace_values(content, values)
        return new_content, values
