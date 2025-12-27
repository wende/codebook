"""Git diff generator for CodeBook files.

This module generates git diffs with resolved values substituted,
showing actual value changes rather than template syntax.
"""

import difflib
import logging
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .renderer import CodeBookRenderer

logger = logging.getLogger(__name__)


@dataclass
class DiffResult:
    """Result of generating a diff.

    Attributes:
        diff: The git diff output
        files_processed: Number of files processed
        error: Error message if diff generation failed
    """

    diff: str
    files_processed: int = 0
    error: str | None = None

    @property
    def success(self) -> bool:
        """Whether diff generation completed without errors."""
        return self.error is None

    @property
    def has_changes(self) -> bool:
        """Whether there are any changes in the diff."""
        return bool(self.diff.strip())


class CodeBookDiffer:
    """Git diff generator with resolved values.

    Generates diffs that show actual value changes by:
    1. Reading current markdown files
    2. Resolving all codebook links to current values
    3. Comparing rendered content against git HEAD

    Example:
        >>> client = CodeBookClient(base_url="http://localhost:3000")
        >>> renderer = CodeBookRenderer(client)
        >>> differ = CodeBookDiffer(renderer)
        >>> result = differ.diff_file(Path("docs/readme.md"))
        >>> if result.has_changes:
        ...     print(result.diff)
    """

    def __init__(self, renderer: CodeBookRenderer):
        """Initialize the differ.

        Args:
            renderer: Renderer to use for resolving templates
        """
        self.renderer = renderer

    def diff_file(self, path: Path, ref: str = "HEAD") -> DiffResult:
        """Generate diff for a single file.

        Args:
            path: Path to the markdown file
            ref: Git ref to compare against (default: HEAD)

        Returns:
            DiffResult with the diff output
        """
        if not path.is_file():
            return DiffResult(diff="", error=f"File not found: {path}")

        try:
            # Read and render current content
            content = path.read_text(encoding="utf-8")
            rendered_content, _ = self.renderer.render_content(content)

            # Get git root
            git_root = self._get_git_root(path)
            if git_root is None:
                return DiffResult(diff="", error="Not in a git repository")

            # Get relative path from git root
            rel_path = path.resolve().relative_to(git_root)

            # Create temp file with rendered content
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".md",
                delete=False,
                encoding="utf-8",
            ) as tmp:
                tmp.write(rendered_content)
                tmp_path = Path(tmp.name)

            try:
                # Generate diff using git diff
                result = subprocess.run(
                    [
                        "git",
                        "diff",
                        "--no-index",
                        "--",
                        f"{ref}:{rel_path}",
                        str(tmp_path),
                    ],
                    cwd=git_root,
                    capture_output=True,
                    text=True,
                )

                # git diff --no-index returns 1 if there are differences
                if result.returncode not in (0, 1):
                    # Try alternative approach: compare with actual HEAD content
                    return self._diff_with_show(path, ref, rendered_content, git_root, rel_path)

                diff_output = result.stdout

                # Clean up the diff output to show the actual file path
                diff_output = diff_output.replace(str(tmp_path), str(rel_path))

                return DiffResult(diff=diff_output, files_processed=1)

            finally:
                tmp_path.unlink(missing_ok=True)

        except Exception as e:
            return DiffResult(diff="", error=str(e))

    def _diff_with_show(
        self,
        path: Path,
        ref: str,
        rendered_content: str,
        git_root: Path,
        rel_path: Path,
    ) -> DiffResult:
        """Generate diff using git show for HEAD content."""
        try:
            # Get HEAD content
            result = subprocess.run(
                ["git", "show", f"{ref}:{rel_path}"],
                cwd=git_root,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                # File might not exist in HEAD (new file)
                head_content = ""
            else:
                head_content = result.stdout

            # Render HEAD content too for fair comparison
            head_rendered, _ = self.renderer.render_content(head_content)

            # Generate unified diff
            diff_lines = difflib.unified_diff(
                head_rendered.splitlines(keepends=True),
                rendered_content.splitlines(keepends=True),
                fromfile=f"a/{rel_path}",
                tofile=f"b/{rel_path}",
            )

            return DiffResult(diff="".join(diff_lines), files_processed=1)

        except Exception as e:
            return DiffResult(diff="", error=str(e))

    def diff_directory(
        self,
        directory: Path,
        ref: str = "HEAD",
        recursive: bool = True,
    ) -> DiffResult:
        """Generate combined diff for all markdown files in a directory.

        Args:
            directory: Path to the directory
            ref: Git ref to compare against (default: HEAD)
            recursive: If True, process subdirectories recursively

        Returns:
            DiffResult with combined diff output
        """
        if not directory.is_dir():
            return DiffResult(diff="", error=f"Not a directory: {directory}")

        diffs: list[str] = []
        files_processed = 0
        errors: list[str] = []

        pattern = "**/*.md" if recursive else "*.md"

        for md_file in sorted(directory.glob(pattern)):
            if md_file.is_file():
                result = self.diff_file(md_file, ref)

                if result.error:
                    errors.append(f"{md_file}: {result.error}")
                elif result.has_changes:
                    diffs.append(result.diff)

                files_processed += result.files_processed

        combined_diff = "\n".join(diffs)
        error = "\n".join(errors) if errors else None

        return DiffResult(
            diff=combined_diff,
            files_processed=files_processed,
            error=error,
        )

    def _get_git_root(self, path: Path) -> Path | None:
        """Find the git repository root for a path."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=path.parent if path.is_file() else path,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return Path(result.stdout.strip())

            return None
        except Exception:
            return None

    def show_rendered(self, path: Path) -> str | None:
        """Show the fully rendered content of a file.

        Useful for previewing what the file would look like with
        all templates resolved.

        Args:
            path: Path to the markdown file

        Returns:
            Rendered content, or None if file couldn't be read
        """
        try:
            content = path.read_text(encoding="utf-8")
            rendered, _ = self.renderer.render_content(content)
            return rendered
        except Exception as e:
            logger.error(f"Failed to render {path}: {e}")
            return None
