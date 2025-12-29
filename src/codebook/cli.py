"""CLI interface for CodeBook.

Provides commands for rendering, watching, and diffing markdown files
with codebook links.

Usage:
    codebook render <directory>    # One-time render
    codebook watch <directory>     # Watch and auto-render
    codebook diff <path>           # Generate git diff
    codebook show <file>           # Show rendered content
    codebook health                # Check backend health
    codebook run                   # Run with codebook.yml config
"""

# Suppress Python 3.13+ free-threaded GIL warning from watchdog
# Must be before any imports that load watchdog
import warnings

warnings.filterwarnings("ignore", message=".*GIL.*")

import logging
import os
import re
import signal
import subprocess
import sys
from pathlib import Path

import click

from . import __version__
from .cicada import CicadaClient
from .client import CodeBookClient
from .config import CodeBookConfig, get_port_from_url
from .differ import CodeBookDiffer
from .kernel import CodeBookKernel
from .renderer import CodeBookRenderer
from .watcher import CodeBookWatcher


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


@click.group()
@click.version_option(version=__version__, prog_name="codebook")
@click.option(
    "--base-url",
    "-b",
    envvar="CODEBOOK_BASE_URL",
    default="http://localhost:3000",
    help="Backend service base URL",
)
@click.option(
    "--timeout",
    "-t",
    type=float,
    default=10.0,
    help="HTTP request timeout in seconds",
)
@click.option(
    "--cache-ttl",
    "-c",
    type=float,
    default=60.0,
    help="Cache TTL in seconds (0 to disable)",
)
@click.option(
    "--cicada-url",
    envvar="CICADA_URL",
    default="http://localhost:9999",
    help="Cicada server URL for code exploration",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
@click.pass_context
def main(
    ctx: click.Context,
    base_url: str,
    timeout: float,
    cache_ttl: float,
    cicada_url: str,
    verbose: bool,
) -> None:
    """CodeBook: Dynamic Markdown Documentation with Live Code References.

    Process markdown files containing codebook:// links and resolve them
    to live values from a backend service.

    Example link format: [`13`](codebook:SCIP.language_count)
    """
    setup_logging(verbose)

    # Store shared objects in context
    ctx.ensure_object(dict)
    ctx.obj["client"] = CodeBookClient(
        base_url=base_url,
        timeout=timeout,
        cache_ttl=cache_ttl,
    )
    ctx.obj["cicada_url"] = cicada_url
    ctx.obj["verbose"] = verbose


@main.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--recursive/--no-recursive",
    default=True,
    help="Process subdirectories recursively",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be changed without modifying files",
)
@click.option(
    "--exec/--no-exec",
    "execute_code",
    default=False,
    help="Execute code blocks via Jupyter kernel",
)
@click.option(
    "--cicada/--no-cicada",
    "use_cicada",
    default=False,
    help="Execute Cicada code exploration queries",
)
@click.pass_context
def render(
    ctx: click.Context,
    directory: Path,
    recursive: bool,
    dry_run: bool,
    execute_code: bool,
    use_cicada: bool,
) -> None:
    """Render all markdown files in a directory.

    Finds all codebook:// links, resolves their templates via HTTP,
    and updates the values in-place.

    With --exec, also executes <exec lang="python">...</exec> code blocks
    and updates their <output>...</output> sections.

    With --cicada, also executes <cicada endpoint="...">...</cicada> blocks
    to query the Cicada code exploration server.

    Example:
        codebook render .codebook/
        codebook render docs/ --dry-run
        codebook render docs/ --exec
        codebook render docs/ --cicada
    """
    client = ctx.obj["client"]

    # Create kernel if code execution is enabled
    kernel = None
    if execute_code:
        click.echo("Starting Jupyter kernel...")
        kernel = CodeBookKernel(cwd=str(directory.resolve()))
        kernel.start()

    # Create Cicada client if enabled
    cicada = None
    if use_cicada:
        cicada_url = ctx.obj["cicada_url"]
        click.echo(f"Connecting to Cicada at {cicada_url}...")
        cicada = CicadaClient(base_url=cicada_url)

    try:
        renderer = CodeBookRenderer(client, kernel=kernel, cicada=cicada)

        click.echo(f"Rendering markdown files in {directory}...")

        if dry_run:
            click.echo("(dry run - no files will be modified)")

        results = renderer.render_directory(directory, recursive=recursive, dry_run=dry_run)

        # Summarize results
        total_found = sum(r.templates_found for r in results)
        total_resolved = sum(r.templates_resolved for r in results)
        total_code_found = sum(r.code_blocks_found for r in results)
        total_code_executed = sum(r.code_blocks_executed for r in results)
        total_cicada_found = sum(r.cicada_queries_found for r in results)
        total_cicada_executed = sum(r.cicada_queries_executed for r in results)
        total_changed = sum(1 for r in results if r.changed)
        total_errors = sum(1 for r in results if r.error)

        click.echo(f"\nProcessed {len(results)} file(s)")
        click.echo(f"  Templates found: {total_found}")
        click.echo(f"  Templates resolved: {total_resolved}")
        if execute_code:
            click.echo(f"  Code blocks found: {total_code_found}")
            click.echo(f"  Code blocks executed: {total_code_executed}")
        if use_cicada:
            click.echo(f"  Cicada queries found: {total_cicada_found}")
            click.echo(f"  Cicada queries executed: {total_cicada_executed}")
        click.echo(f"  Files changed: {total_changed}")

        if total_errors > 0:
            click.echo(f"  Errors: {total_errors}", err=True)
            for r in results:
                if r.error:
                    click.echo(f"    {r.path}: {r.error}", err=True)
            sys.exit(1)
    finally:
        if kernel:
            kernel.stop()


@main.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--recursive/--no-recursive",
    default=True,
    help="Watch subdirectories recursively",
)
@click.option(
    "--debounce",
    "-d",
    type=float,
    default=0.5,
    help="Debounce delay in seconds",
)
@click.option(
    "--initial-render/--no-initial-render",
    default=True,
    help="Render all files before starting watch",
)
@click.option(
    "--exec/--no-exec",
    "execute_code",
    default=False,
    help="Execute code blocks via Jupyter kernel",
)
@click.option(
    "--cicada/--no-cicada",
    "use_cicada",
    default=False,
    help="Execute Cicada code exploration queries",
)
@click.pass_context
def watch(
    ctx: click.Context,
    directory: Path,
    recursive: bool,
    debounce: float,
    initial_render: bool,
    execute_code: bool,
    use_cicada: bool,
) -> None:
    """Watch directory for changes and auto-render.

    Monitors markdown files for modifications and automatically
    re-renders them when changes are detected.

    With --exec, also executes <exec lang="python">...</exec> code blocks
    and updates their <output>...</output> sections.

    With --cicada, also executes <cicada endpoint="...">...</cicada> blocks
    to query the Cicada code exploration server.

    Example:
        codebook watch .codebook/
        codebook watch docs/ --debounce 1.0
        codebook watch docs/ --exec
        codebook watch docs/ --cicada
    """
    client = ctx.obj["client"]

    # Create kernel if code execution is enabled
    kernel = None
    if execute_code:
        click.echo("Starting Jupyter kernel...")
        kernel = CodeBookKernel(cwd=str(directory.resolve()))
        kernel.start()

    # Create Cicada client if enabled
    cicada = None
    if use_cicada:
        cicada_url = ctx.obj["cicada_url"]
        click.echo(f"Connecting to Cicada at {cicada_url}...")
        cicada = CicadaClient(base_url=cicada_url)

    try:
        renderer = CodeBookRenderer(client, kernel=kernel, cicada=cicada)

        # Check backend health before starting
        click.echo(f"Checking backend at {client.base_url}...")
        if not client.health_check():
            click.echo("Error: Backend service is not responding. Is the server running?", err=True)
            sys.exit(1)
        click.echo("Backend is healthy.\n")

        # Initial render if requested
        if initial_render:
            click.echo("Performing initial render...")
            results = renderer.render_directory(directory, recursive=recursive)
            total_changed = sum(1 for r in results if r.changed)
            total_files = len(results)
            click.echo(f"Initial render complete: {total_changed}/{total_files} file(s) updated\n")

        def on_render(path: Path) -> None:
            click.echo(f"Rendered: {path}")

        watcher = CodeBookWatcher(
            renderer=renderer,
            debounce_delay=debounce,
            on_render=on_render,
        )

        click.echo(f"Watching {directory} for changes (Ctrl+C to stop)...")
        if execute_code:
            click.echo("(code execution enabled)")
        watcher.watch(directory, recursive=recursive)

        watcher.start()
    except KeyboardInterrupt:
        click.echo("\nStopping watcher...")
        watcher.stop()
    finally:
        if kernel:
            kernel.stop()


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--ref",
    "-r",
    default="HEAD",
    help="Git ref to compare against",
)
@click.option(
    "--recursive/--no-recursive",
    default=True,
    help="Process subdirectories recursively (for directories)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Write diff to file instead of stdout",
)
@click.pass_context
def diff(ctx: click.Context, path: Path, ref: str, recursive: bool, output: Path | None) -> None:
    """Generate git diff with resolved values.

    Shows how values have changed by comparing rendered content
    against the git reference (default: HEAD).

    Example:
        codebook diff .codebook/
        codebook diff .codebook/ -o changes.patch
        codebook diff docs/readme.md --ref main
    """
    client = ctx.obj["client"]
    renderer = CodeBookRenderer(client)
    differ = CodeBookDiffer(renderer)

    if path.is_dir():
        result = differ.diff_directory(path, ref=ref, recursive=recursive)
    else:
        result = differ.diff_file(path, ref=ref)

    if result.error:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)

    if result.has_changes:
        if output:
            output.write_text(result.diff, encoding="utf-8")
            click.echo(f"Diff written to {output}")
        else:
            click.echo(result.diff)
    else:
        click.echo("No changes", err=True)


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.pass_context
def show(ctx: click.Context, path: Path) -> None:
    """Show rendered content of a file.

    Displays the file with all codebook links resolved to their
    current values.

    Example:
        codebook show .codebook/readme.md
    """
    client = ctx.obj["client"]
    renderer = CodeBookRenderer(client)
    differ = CodeBookDiffer(renderer)

    if not path.is_file():
        click.echo(f"Error: Not a file: {path}", err=True)
        sys.exit(1)

    rendered = differ.show_rendered(path)

    if rendered is None:
        click.echo("Error: Failed to render file", err=True)
        sys.exit(1)

    click.echo(rendered)


@main.command()
@click.pass_context
def health(ctx: click.Context) -> None:
    """Check backend service health.

    Verifies that the backend service is reachable and responding.

    Example:
        codebook health
        codebook --base-url http://api.example.com health
    """
    client = ctx.obj["client"]

    click.echo(f"Checking {client.base_url}...")

    if client.health_check():
        click.echo("Backend service is healthy")
    else:
        click.echo("Backend service is not responding", err=True)
        sys.exit(1)


@main.command("clear-cache")
@click.pass_context
def clear_cache(ctx: click.Context) -> None:
    """Clear the template resolution cache.

    Forces fresh resolution of all templates on next render.

    Example:
        codebook clear-cache
    """
    client = ctx.obj["client"]
    client.clear_cache()
    click.echo("Cache cleared")


@main.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to codebook.yml config file",
)
@click.pass_context
def run(ctx: click.Context, config: Path | None) -> None:
    """Run CodeBook with configuration from codebook.yml.

    Starts all configured services (backend, cicada) and the file watcher.
    Press Ctrl+C to stop all services.

    Example:
        codebook run
        codebook run -c path/to/codebook.yml
    """
    # Load config
    cfg = CodeBookConfig.load(config)

    if config:
        click.echo(f"Loaded config from {config}")
    else:
        found = CodeBookConfig._find_config_file()
        if found:
            click.echo(f"Loaded config from {found}")
        else:
            click.echo("No codebook.yml found, using defaults")

    processes: list[subprocess.Popen] = []

    def cleanup(signum=None, frame=None):
        """Clean up child processes."""
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        # Start cicada if configured
        if cfg.cicada.start:
            cicada_port = get_port_from_url(cfg.cicada.url)
            click.echo(f"Starting Cicada on port {cicada_port}...")
            proc = subprocess.Popen(
                ["cicada", "serve", "--port", str(cicada_port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            processes.append(proc)

        # Start mock backend if configured
        if cfg.backend.start:
            backend_port = get_port_from_url(cfg.backend.url)
            click.echo(f"Starting backend on port {backend_port}...")
            mock_server = Path(__file__).parent.parent.parent.parent / "examples" / "mock_server.py"
            proc = subprocess.Popen(
                ["python", str(mock_server), "--port", str(backend_port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            processes.append(proc)

        # Wait for servers to start
        if processes:
            import time

            time.sleep(1)

        # Create client
        client = CodeBookClient(
            base_url=cfg.backend.url,
            timeout=cfg.timeout,
            cache_ttl=cfg.cache_ttl,
        )

        # Create kernel if exec enabled
        kernel = None
        directory = Path(cfg.main_dir)
        if cfg.exec:
            click.echo("Starting Jupyter kernel...")
            kernel = CodeBookKernel(cwd=str(directory.resolve()))
            kernel.start()

        # Create Cicada client if enabled
        cicada = None
        if cfg.cicada.enabled:
            click.echo(f"Connecting to Cicada at {cfg.cicada.url}...")
            cicada = CicadaClient(base_url=cfg.cicada.url)

        try:
            renderer = CodeBookRenderer(client, kernel=kernel, cicada=cicada)

            # Check backend health
            click.echo(f"Checking backend at {client.base_url}...")
            if not client.health_check():
                click.echo("Warning: Backend service is not responding", err=True)
            else:
                click.echo("Backend is healthy.")

            # Initial render
            click.echo(f"\nPerforming initial render of {directory}...")
            results = renderer.render_directory(directory, recursive=cfg.recursive)
            total_changed = sum(1 for r in results if r.changed)
            click.echo(f"Initial render complete: {total_changed}/{len(results)} file(s) updated\n")

            def on_render(path: Path) -> None:
                click.echo(f"Rendered: {path}")

            watcher = CodeBookWatcher(
                renderer=renderer,
                debounce_delay=0.5,
                on_render=on_render,
            )

            click.echo(f"Watching {directory} for changes (Ctrl+C to stop)...")
            if cfg.exec:
                click.echo("(code execution enabled)")
            if cfg.cicada.enabled:
                click.echo("(cicada queries enabled)")

            watcher.watch(directory, recursive=cfg.recursive)
            watcher.start()

        finally:
            if kernel:
                kernel.stop()

    finally:
        cleanup()


@main.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="codebook.yml",
    help="Output path for config file",
)
def init(output: Path) -> None:
    """Create a default codebook.yml configuration file.

    Example:
        codebook init
        codebook init -o my-config.yml
    """
    import yaml

    config = CodeBookConfig(
        main_dir="codebook",
        exec=True,
        recursive=True,
        backend=CodeBookConfig._from_dict({}).backend,
        cicada=CodeBookConfig._from_dict({"cicada": {"enabled": True, "start": True}}).cicada,
    )
    config.cicada.enabled = True
    config.cicada.start = True

    with open(output, "w") as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False, sort_keys=False)

    click.echo(f"Created {output}")


@main.group()
def task() -> None:
    """Manage CodeBook tasks.

    Tasks capture the state of markdown files before and after changes,
    useful for tracking documentation updates.

    Example:
        codebook task new "My Task" ./docs
        codebook task list
    """
    pass


def _create_task_worktree(
    title: str, task_name: str, date_prefix: str, scope: Path
) -> tuple[Path, Path] | None:
    """Create a new git worktree for a task.

    Args:
        title: Human-readable task title
        task_name: UPPER_SNAKE_CASE task name
        date_prefix: YYYYMMDDHHMM timestamp
        scope: Path to the scope being documented

    Returns:
        Tuple of (worktree_path, worktree_scope_path), or None if creation failed
    """
    try:
        # Get git root
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        git_root = Path(result.stdout.strip())

        # Resolve scope relative to git root
        scope_resolved = scope.resolve()
        try:
            scope_rel = scope_resolved.relative_to(git_root)
        except ValueError:
            click.echo(f"Error: Scope {scope} is not within git repository", err=True)
            return None

        # Get the root directory name
        root_dir_name = git_root.name

        # Create worktree directory name: {rootdir}-{task-title}
        worktree_name = f"{root_dir_name}-{task_name.lower()}"
        worktree_path = git_root.parent / worktree_name

        # Get current branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True,
        )
        current_branch = result.stdout.strip()

        # Create new branch name for the worktree: task-{task-title}
        branch_name = f"task-{task_name.lower()}"

        # Create the worktree
        result = subprocess.run(
            ["git", "worktree", "add", "-b", branch_name, str(worktree_path), current_branch],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            click.echo(f"Error creating worktree: {result.stderr}", err=True)
            return None

        # Get list of modified and untracked files in scope
        result = subprocess.run(
            ["git", "status", "--porcelain", str(scope)],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0 and result.stdout.strip():
            # Copy uncommitted changes to worktree
            for line in result.stdout.split("\n"):
                if line and len(line) >= 3:
                    line[:2]
                    file_path = line[3:]

                    # Handle renamed files
                    if " -> " in file_path:
                        file_path = file_path.split(" -> ")[1]

                    src_file = git_root / file_path
                    dst_file = worktree_path / file_path

                    if src_file.exists():
                        # Ensure parent directory exists in worktree
                        dst_file.parent.mkdir(parents=True, exist_ok=True)

                        # Copy the file content
                        import shutil

                        shutil.copy2(src_file, dst_file)

            # Revert the scoped changes in the source branch
            # Only revert files within the scope
            subprocess.run(
                ["git", "checkout", "HEAD", "--", str(scope)],
                capture_output=True,
                text=True,
            )

            # Also remove any untracked files in scope
            result = subprocess.run(
                ["git", "status", "--porcelain", str(scope)],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line and line.startswith("??"):
                        file_path = line[3:]
                        untracked_file = git_root / file_path
                        if untracked_file.exists():
                            untracked_file.unlink()

        # Return worktree path and the scope path within the worktree
        worktree_scope = worktree_path / scope_rel
        return (worktree_path, worktree_scope)

    except subprocess.CalledProcessError as e:
        click.echo(f"Git error: {e}", err=True)
        return None
    except Exception as e:
        click.echo(f"Error creating worktree: {e}", err=True)
        return None


@task.command("new")
@click.argument("title", type=str)
@click.argument("scope", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--all",
    "include_all",
    is_flag=True,
    help="Include all files, not just modified ones",
)
@click.option(
    "--worktree",
    is_flag=True,
    help="Create a new worktree for the task",
)
@click.pass_context
def task_new(
    ctx: click.Context, title: str, scope: Path, include_all: bool, worktree: bool
) -> None:
    """Create a new task capturing modified files and their diffs.

    Creates a task file at .codebook/tasks/YYYYMMDDHHMM-TITLE.md containing
    the original content and git diff for each MODIFIED file in scope.

    By default, only includes files with uncommitted changes.
    Use --all to include all files regardless of git status.

    The task is prepended with a generic prompt describing what to be changed.
    This wrapper can be customized by adding task-prefix and task-suffix to codebook.yml.

    With --worktree, creates a new git worktree for the task, copies uncommitted
    changes to the worktree, and reverts them on the source branch. The task is
    created in the worktree instead of the source branch.

    Example:
        codebook task new "Feature Documentation" ./docs
        codebook task new "API Update" ./README.md
        codebook task new "Full Snapshot" ./docs --all
        codebook task new "Theme Support" ./docs --worktree
    """
    import re
    from datetime import datetime

    # Load config for task prefix/suffix
    cfg = CodeBookConfig.load()

    # Convert title to UPPER_SNAKE_CASE
    task_name = re.sub(r"[^\w\s]", "", title)
    task_name = re.sub(r"\s+", "_", task_name).upper()

    # Add datetime prefix (YYYYMMDDHHMM)
    date_prefix = datetime.now().strftime("%Y%m%d%H%M")

    # Handle worktree creation if requested
    worktree_info = None
    if worktree:
        worktree_info = _create_task_worktree(title, task_name, date_prefix, scope)
        if worktree_info is None:
            click.echo("Failed to create worktree", err=True)
            return
        worktree_path, worktree_scope = worktree_info
        click.echo(f"Created worktree at {worktree_path}")
        # Switch to worktree context
        Path.cwd()
        os.chdir(worktree_path)
        # Update scope to point to the worktree location
        scope = worktree_scope

    # Create tasks directory
    tasks_dir = Path(cfg.tasks_dir)
    tasks_dir.mkdir(parents=True, exist_ok=True)

    task_file = tasks_dir / f"{date_prefix}-{task_name}.md"

    # Get modified files from git
    def get_modified_files(scope_path: Path) -> tuple[set[Path], set[Path]]:
        """Get list of modified and untracked files in scope.

        Returns:
            Tuple of (modified_files, untracked_files) as sets of resolved paths.
        """
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", str(scope_path)],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return set(), set()
            modified = set()
            untracked = set()
            for line in result.stdout.split("\n"):
                if line and len(line) >= 3:
                    status = line[:2]
                    # Format: "XY filename" where XY is 2-char status + space
                    file_path = line[3:]
                    # Handle renamed files: "R  old -> new"
                    if " -> " in file_path:
                        file_path = file_path.split(" -> ")[1]
                    resolved = Path(file_path).resolve()
                    if status == "??":
                        untracked.add(resolved)
                    else:
                        modified.add(resolved)
            return modified, untracked
        except Exception:
            return set(), set()

    # Get raw git diff for a file
    def get_git_diff(file_path: Path, is_untracked: bool = False) -> str | None:
        """Get raw git diff for a file.

        Args:
            file_path: Path to the file
            is_untracked: If True, use --no-index to show new file as diff
        """
        try:
            if is_untracked:
                # For untracked files, compare against /dev/null
                result = subprocess.run(
                    ["git", "diff", "--no-index", "/dev/null", str(file_path)],
                    capture_output=True,
                    text=True,
                )
                # --no-index returns 1 when files differ, which is expected
                if result.stdout.strip():
                    return result.stdout
                return None
            else:
                result = subprocess.run(
                    ["git", "diff", str(file_path)],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout
                return None
        except Exception:
            return None

    def is_version_only_diff(diff_output: str) -> bool:
        """Check if a diff only contains codebook version changes."""
        # Extract actual changed lines (excluding diff metadata)
        changed_lines = []
        for line in diff_output.split("\n"):
            # Skip diff headers and context lines
            if line.startswith("diff ") or line.startswith("index "):
                continue
            if line.startswith("--- ") or line.startswith("+++ "):
                continue
            if line.startswith("@@ "):
                continue
            # Capture actual additions/deletions (not context lines)
            if line.startswith("+") or line.startswith("-"):
                # Skip empty additions/deletions
                content = line[1:].strip()
                if content:
                    changed_lines.append(content)

        # If no actual changes, consider it version-only (empty diff edge case)
        if not changed_lines:
            return True

        # Check if ALL changed lines are codebook version stamps
        version_pattern = re.compile(
            r"Rendered by CodeBook \[`[^`]*`\]\(codebook:codebook\.version\)"
        )
        return all(version_pattern.search(line) for line in changed_lines)

    # Helper to check if file is in tasks directory
    def is_in_tasks_dir(file_path: Path) -> bool:
        """Check if a file path is within the tasks directory."""
        try:
            tasks_dir_resolved = Path(cfg.tasks_dir).resolve()
            file_resolved = file_path.resolve()
            return (
                tasks_dir_resolved in file_resolved.parents or file_resolved == tasks_dir_resolved
            )
        except (ValueError, OSError):
            return False

    # Collect files to process (excluding tasks directory)
    if scope.is_file():
        candidates = [scope] if not is_in_tasks_dir(scope) else []
    else:
        candidates = sorted(f for f in scope.glob("**/*.md") if not is_in_tasks_dir(f))

    # Filter to only modified/untracked files unless --all
    if include_all:
        files = candidates
        untracked_files: set[Path] = set()
    else:
        modified, untracked_files = get_modified_files(scope)
        all_changed = modified | untracked_files
        files = [f for f in candidates if f.resolve() in all_changed]

    if not files:
        click.echo(f"No modified markdown files found in {scope}", err=True)
        click.echo("Use --all to include all files regardless of git status", err=True)
        return

    # Get git root for relative paths
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        git_root = Path(result.stdout.strip())
    except Exception:
        click.echo("Error: Not in a git repository", err=True)
        return

    # Build task content
    lines = []
    # Add prefix if configured
    if cfg.task_prefix:
        lines.append(cfg.task_prefix)
    lines.append(f"# {title}\n\n")
    file_count = 0

    for file_path in files:
        if not file_path.is_file():
            continue

        # Get raw git diff (use --no-index for untracked files)
        is_untracked = file_path.resolve() in untracked_files
        diff_output = get_git_diff(file_path, is_untracked=is_untracked)

        if not diff_output:
            continue

        rel_path = str(file_path.resolve().relative_to(git_root))
        file_count += 1
        lines.append(f'<diff file="{rel_path}">\n')
        lines.append("```diff\n")
        lines.append(diff_output)
        if not diff_output.endswith("\n"):
            lines.append("\n")
        lines.append("```\n")
        lines.append("</diff>\n\n")

    if file_count == 0:
        click.echo(f"No modified markdown files found in {scope}", err=True)
        click.echo("Use --all to include all files regardless of git status", err=True)
        return

    # Add suffix if configured
    if cfg.task_suffix:
        lines.append(cfg.task_suffix)
        if not cfg.task_suffix.endswith("\n"):
            lines.append("\n")

    # Write task file
    task_file.write_text("".join(lines), encoding="utf-8")
    click.echo(f"Created task: {task_file} ({file_count} file(s))")


def _update_single_task(task_file: Path, scope: Path) -> bool:
    """Update a single task file with new diffs from documentation files.

    Args:
        task_file: Path to the task file to update
        scope: Path to the scope directory or file

    Returns:
        True if the task was updated, False otherwise
    """
    import re

    # Load config for tasks_dir exclusion
    cfg = CodeBookConfig.load()

    # Helper to check if file is in tasks directory
    def is_in_tasks_dir(file_path: Path) -> bool:
        """Check if a file path is within the tasks directory."""
        try:
            tasks_dir_resolved = Path(cfg.tasks_dir).resolve()
            file_resolved = file_path.resolve()
            return (
                tasks_dir_resolved in file_resolved.parents or file_resolved == tasks_dir_resolved
            )
        except (ValueError, OSError):
            return False

    # Get modified files from git
    def get_modified_files(scope_path: Path) -> tuple[set[Path], set[Path]]:
        """Get list of modified and untracked files in scope."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", str(scope_path)],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return set(), set()
            modified = set()
            untracked = set()
            for line in result.stdout.split("\n"):
                if line and len(line) >= 3:
                    status = line[:2]
                    file_path = line[3:]
                    if " -> " in file_path:
                        file_path = file_path.split(" -> ")[1]
                    resolved = Path(file_path).resolve()
                    if status == "??":
                        untracked.add(resolved)
                    else:
                        modified.add(resolved)
            return modified, untracked
        except Exception:
            return set(), set()

    def get_git_diff(file_path: Path, is_untracked: bool = False) -> str | None:
        """Get raw git diff for a file."""
        try:
            if is_untracked:
                result = subprocess.run(
                    ["git", "diff", "--no-index", "/dev/null", str(file_path)],
                    capture_output=True,
                    text=True,
                )
                if result.stdout.strip():
                    return result.stdout
                return None
            else:
                result = subprocess.run(
                    ["git", "diff", str(file_path)],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout
                return None
        except Exception:
            return None

    def extract_files_from_task(content: str) -> set[str]:
        """Extract file paths already documented in the task."""
        files = set()
        # Match new format: <diff file="path/to/file">
        tag_pattern = re.compile(r'<diff file="([^"]+)">')
        for match in tag_pattern.finditer(content):
            files.add(match.group(1))
        # Also match old format for backwards compatibility: diff --git a/path b/path
        diff_pattern = re.compile(r"^diff --git a/([^\s]+) b/([^\s]+)", re.MULTILINE)
        for match in diff_pattern.finditer(content):
            files.add(match.group(2))
        return files

    # Read existing task content
    task_content = task_file.read_text(encoding="utf-8")

    # Extract files already in task
    existing_files = extract_files_from_task(task_content)

    # Collect files to process (excluding tasks directory)
    if scope.is_file():
        candidates = [scope] if not is_in_tasks_dir(scope) else []
    else:
        candidates = sorted(f for f in scope.glob("**/*.md") if not is_in_tasks_dir(f))

    # Get modified/untracked files
    modified, untracked_files = get_modified_files(scope)
    all_changed = modified | untracked_files

    # Get git root for relative paths
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        git_root = Path(result.stdout.strip())
    except Exception:
        click.echo("Error: Not in a git repository", err=True)
        return False

    # Separate files into new (to add) and existing (to update)
    files_to_add = []
    files_to_update = []
    for f in candidates:
        if f.resolve() not in all_changed:
            continue
        try:
            rel_path = str(f.resolve().relative_to(git_root))
            if rel_path in existing_files:
                files_to_update.append((f, rel_path))
            else:
                files_to_add.append(f)
        except ValueError:
            continue

    if not files_to_add and not files_to_update:
        click.echo(f"No modified documentation files to update for {task_file}", err=True)
        return False

    # Update existing file diffs in place
    updated_content = task_content
    updated_count = 0

    for file_path, rel_path in files_to_update:
        is_untracked = file_path.resolve() in untracked_files
        diff_output = get_git_diff(file_path, is_untracked=is_untracked)

        if not diff_output:
            continue

        # Build new diff block with tag wrapper
        diff_content = diff_output if diff_output.endswith("\n") else diff_output + "\n"
        new_diff_block = f'<diff file="{rel_path}">\n```diff\n{diff_content}```\n</diff>\n\n'

        # Try new format first: <diff file="...">...</diff>
        escaped_path = re.escape(rel_path)
        tag_pattern = re.compile(
            rf'<diff file="{escaped_path}">.*?</diff>\n*',
            re.DOTALL,
        )
        if tag_pattern.search(updated_content):
            updated_content = tag_pattern.sub(new_diff_block, updated_content)
            updated_count += 1
            continue

        # Fall back to old format: ```diff\ndiff --git a/path b/path\n...```
        # Match closing ``` only at start of line to avoid matching ``` inside diff
        old_pattern = re.compile(
            rf"```diff\ndiff --git a/{escaped_path} b/{escaped_path}\n.*?\n```\n*",
            re.DOTALL,
        )
        if old_pattern.search(updated_content):
            updated_content = old_pattern.sub(new_diff_block, updated_content)
            updated_count += 1

    # Build new diff content for new files
    new_diffs = []
    added_count = 0

    for file_path in files_to_add:
        is_untracked = file_path.resolve() in untracked_files
        diff_output = get_git_diff(file_path, is_untracked=is_untracked)

        if not diff_output:
            continue

        rel_path = str(file_path.resolve().relative_to(git_root))
        added_count += 1
        new_diffs.append(f'<diff file="{rel_path}">\n')
        new_diffs.append("```diff\n")
        new_diffs.append(diff_output)
        if not diff_output.endswith("\n"):
            new_diffs.append("\n")
        new_diffs.append("```\n")
        new_diffs.append("</diff>\n\n")

    if added_count == 0 and updated_count == 0:
        click.echo(f"No diffs to update for {task_file}", err=True)
        return False

    # Append new files before footer sections
    if new_diffs:
        footer_markers = ["--- FEATURE TASK ---", "--- NOTES ---", "--- SOLUTION ---"]
        insert_pos = len(updated_content)

        for marker in footer_markers:
            pos = updated_content.find(marker)
            if pos != -1 and pos < insert_pos:
                insert_pos = pos

        if insert_pos < len(updated_content):
            updated_content = (
                updated_content[:insert_pos] + "".join(new_diffs) + updated_content[insert_pos:]
            )
        else:
            updated_content = updated_content.rstrip() + "\n\n" + "".join(new_diffs)

    task_file.write_text(updated_content, encoding="utf-8")

    # Build status message
    parts = []
    if updated_count > 0:
        parts.append(f"~{updated_count} updated")
    if added_count > 0:
        parts.append(f"+{added_count} added")
    click.echo(f"Updated task: {task_file} ({', '.join(parts)})")
    return True


@task.command("update")
@click.argument("task_file", type=click.Path(exists=True, path_type=Path), required=False)
@click.argument("scope", type=click.Path(exists=True, path_type=Path), required=False)
@click.pass_context
def task_update(ctx: click.Context, task_file: Path | None, scope: Path | None) -> None:
    """Update a task file with new diffs to documentation files.

    Updates existing diffs for files already in the task and appends
    new diffs for modified files not yet included.

    TASK_FILE is the path to the task file to update. If not provided,
    all modified and untracked task files in the tasks directory will be updated.

    SCOPE is the directory to look for modified documentation files.
    If not provided, uses the main_dir from codebook.yml configuration.

    Example:
        codebook task update ./tasks/202412281530-FEATURE.md ./docs
        codebook task update  # Updates all modified/untracked task files
    """
    cfg = CodeBookConfig.load()

    # Default scope to main_dir from config
    if scope is None:
        scope = Path(cfg.main_dir)
        if not scope.exists():
            click.echo(f"Error: Default scope directory does not exist: {scope}", err=True)
            sys.exit(1)

    # If no task file provided, find all modified/untracked task files
    if task_file is None:
        tasks_dir = Path(cfg.tasks_dir)
        task_files = _get_modified_task_files(tasks_dir)

        if not task_files:
            click.echo(f"No modified or untracked task files found in {tasks_dir}")
            sys.exit(0)

        click.echo(f"Found {len(task_files)} task file(s) to update:")
        for f in task_files:
            click.echo(f"  - {f}")
        click.echo()

        # Update each task file
        success_count = 0
        for tf in task_files:
            if _update_single_task(tf, scope):
                success_count += 1

        if success_count == 0:
            click.echo("No tasks were updated", err=True)
            sys.exit(1)
    else:
        # Single task file update
        if not _update_single_task(task_file, scope):
            sys.exit(1)


@task.command("list")
def task_list() -> None:
    """List all existing tasks.

    Shows all task files in the configured tasks directory.

    Example:
        codebook task list
    """
    cfg = CodeBookConfig.load()
    tasks_dir = Path(cfg.tasks_dir)

    if not tasks_dir.exists():
        click.echo("No tasks directory found.")
        return

    task_files = sorted(tasks_dir.glob("*.md"))

    if not task_files:
        click.echo("No tasks found.")
        return

    click.echo("Tasks:")
    for task_file in task_files:
        # Parse filename to extract date and title
        name = task_file.stem
        # Check if filename has datetime prefix (YYYYMMDDHHMM-)
        if len(name) > 13 and name[12] == "-" and name[:12].isdigit():
            date_part = name[:12]
            title_part = name[13:]
            formatted_date = (
                f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} "
                f"{date_part[8:10]}:{date_part[10:12]}"
            )
            click.echo(f"  [{formatted_date}] {title_part}")
        # Fallback: Check for old format (YYYYMMDD-)
        elif len(name) > 9 and name[8] == "-" and name[:8].isdigit():
            date_part = name[:8]
            title_part = name[9:]
            formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
            click.echo(f"  [{formatted_date}] {title_part}")
        else:
            click.echo(f"  {name}")


@task.command("delete")
@click.argument("title", type=str, required=False)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Delete without confirmation",
)
def task_delete(title: str | None, force: bool) -> None:
    """Delete a task file.

    If TITLE is provided, deletes the matching task file (ignoring date prefix).
    If no TITLE is provided, presents an interactive picker to select a task.

    Example:
        codebook task delete "API Update"
        codebook task delete
        codebook task delete "API Update" --force
    """
    import re

    cfg = CodeBookConfig.load()
    tasks_dir = Path(cfg.tasks_dir)

    if not tasks_dir.exists():
        click.echo("No tasks directory found.", err=True)
        return

    task_files = sorted(tasks_dir.glob("*.md"))

    if not task_files:
        click.echo("No tasks found.", err=True)
        return

    def parse_task_title(filename: str) -> str:
        """Extract title from task filename (stripping date prefix if present)."""
        # Check if filename has datetime prefix (YYYYMMDDHHMM-)
        if len(filename) > 13 and filename[12] == "-" and filename[:12].isdigit():
            return filename[13:]
        # Fallback: Check for old format (YYYYMMDD-)
        if len(filename) > 9 and filename[8] == "-" and filename[:8].isdigit():
            return filename[9:]
        return filename

    def format_task_choice(task_file: Path) -> str:
        """Format a task file for display in the picker."""
        name = task_file.stem
        # Check for new format (YYYYMMDDHHMM-)
        if len(name) > 13 and name[12] == "-" and name[:12].isdigit():
            date_part = name[:12]
            title_part = name[13:]
            formatted_date = (
                f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} "
                f"{date_part[8:10]}:{date_part[10:12]}"
            )
            return f"[{formatted_date}] {title_part}"
        # Fallback: Check for old format (YYYYMMDD-)
        if len(name) > 9 and name[8] == "-" and name[:8].isdigit():
            date_part = name[:8]
            title_part = name[9:]
            formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
            return f"[{formatted_date}] {title_part}"
        return name

    target_file: Path | None = None

    if title:
        # Convert title to UPPER_SNAKE_CASE for matching
        search_name = re.sub(r"[^\w\s]", "", title)
        search_name = re.sub(r"\s+", "_", search_name).upper()

        # Find matching task file
        for task_file in task_files:
            task_title = parse_task_title(task_file.stem)
            if task_title == search_name:
                target_file = task_file
                break

        if not target_file:
            click.echo(f"Task not found: {title}", err=True)
            click.echo("Available tasks:")
            for task_file in task_files:
                click.echo(f"  {format_task_choice(task_file)}")
            return
    else:
        # Interactive picker
        choices = {format_task_choice(f): f for f in task_files}
        choice_list = list(choices.keys())

        click.echo("Select a task to delete:")
        for i, choice in enumerate(choice_list, 1):
            click.echo(f"  {i}. {choice}")

        selection = click.prompt(
            "Enter number",
            type=click.IntRange(1, len(choice_list)),
        )
        target_file = choices[choice_list[selection - 1]]

    # Confirm deletion
    if not force:
        task_display = format_task_choice(target_file)
        if not click.confirm(f"Delete task '{task_display}'?"):
            click.echo("Cancelled.")
            return

    # Delete the file
    target_file.unlink()
    click.echo(f"Deleted: {target_file}")


def _parse_task_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from a task file.

    Args:
        content: The task file content

    Returns:
        Dict containing parsed frontmatter fields, or empty dict if none found
    """
    import yaml

    # Match frontmatter at the start of the file
    frontmatter_pattern = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
    match = frontmatter_pattern.match(content)
    if not match:
        return {}

    yaml_content = match.group(1)
    try:
        data = yaml.safe_load(yaml_content) or {}
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


def _is_ancestor_commit(ancestor_sha: str, descendant_sha: str, git_root: Path) -> bool:
    """Check if ancestor_sha is an ancestor of (or equal to) descendant_sha.

    Args:
        ancestor_sha: The potential ancestor commit SHA
        descendant_sha: The potential descendant commit SHA
        git_root: Path to the git root directory

    Returns:
        True if ancestor_sha is an ancestor of or equal to descendant_sha
    """
    # If they're the same commit (comparing short SHAs)
    if ancestor_sha.startswith(descendant_sha) or descendant_sha.startswith(ancestor_sha):
        return True

    try:
        # git merge-base --is-ancestor returns 0 if ancestor is an ancestor of descendant
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor_sha, descendant_sha],
            cwd=git_root,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def _extract_reviewed_files(tasks_dir: Path) -> dict[str, list[tuple[str, str]]]:
    """Extract reviewed file:sha pairs from task frontmatter.

    Args:
        tasks_dir: Path to the tasks directory

    Returns:
        Dict mapping file paths to list of (sha, task_name) tuples
    """
    reviewed_files: dict[str, list[tuple[str, str]]] = {}

    if not tasks_dir.exists():
        return reviewed_files

    task_files = sorted(tasks_dir.glob("*.md"))

    for task_file in task_files:
        task_name = task_file.stem
        try:
            content = task_file.read_text(encoding="utf-8")
            frontmatter = _parse_task_frontmatter(content)

            reviewed = frontmatter.get("reviewed", [])
            if isinstance(reviewed, str):
                reviewed = [reviewed]
            if not isinstance(reviewed, list):
                continue

            for entry in reviewed:
                if not isinstance(entry, str) or ":" not in entry:
                    continue
                # Parse format: path/to/file.md:sha
                parts = entry.rsplit(":", 1)
                if len(parts) == 2:
                    file_path, sha = parts
                    file_path = file_path.strip()
                    sha = sha.strip()
                    if file_path and sha:
                        if file_path not in reviewed_files:
                            reviewed_files[file_path] = []
                        reviewed_files[file_path].append((sha, task_name))
        except Exception:
            continue

    return reviewed_files


@task.command("coverage")
@click.argument(
    "path_glob",
    type=str,
    default=".",
    required=False,
)
@click.option(
    "--detailed",
    is_flag=True,
    help="Show detailed line-by-line coverage report",
)
@click.option(
    "--short",
    is_flag=True,
    help="Show only the coverage score",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output coverage data as JSON (for CI integration)",
)
def task_coverage(path_glob: str, detailed: bool, short: bool, output_json: bool) -> None:
    """Analyze task coverage for the project.

    Shows what percentage of code lines are covered by task documentation.
    Uses git blame to track which commits are associated with tasks.

    Coverage can come from two sources:
    1. Commits that touched task files (traditional method)
    2. Files marked as 'reviewed' in task frontmatter with a specific commit SHA

    PATH_GLOB is an optional path or glob pattern to limit analysis scope.

    Example:
        codebook task coverage
        codebook task coverage src/
        codebook task coverage --detailed
        codebook task coverage --short
    """

    cfg = CodeBookConfig.load()
    main_dir = Path(cfg.main_dir)

    if not main_dir.exists():
        click.echo("No codebook directory found.", err=True)
        return

    # Get git root
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        git_root = Path(result.stdout.strip())
    except Exception:
        click.echo("Error: Not in a git repository", err=True)
        return

    # Extract commits from task files using git blame
    tasks_dir = Path(cfg.tasks_dir)

    def extract_commits_from_tasks() -> dict[str, str]:
        """Extract commits associated with task files using git blame.

        Runs git blame on each task markdown file to find all commits that have
        modified the tasks. This connects tasks to the actual commits that
        implemented the features.

        Returns:
            Dict mapping commit SHA (short) to task file name
        """
        commit_to_task: dict[str, str] = {}

        if not tasks_dir.exists():
            return commit_to_task

        task_files = sorted(tasks_dir.glob("*.md"))

        for task_file in task_files:
            task_name = task_file.stem

            try:
                # Get relative path from git root for blame
                rel_path = task_file.resolve().relative_to(git_root)

                # Run git blame to get all commits that touched this task file
                # Use -CCC to detect copies/renames across files
                cmd = ["git", "blame", "-CCC", "--porcelain", str(rel_path)]
                result = subprocess.run(
                    cmd,
                    cwd=git_root,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    # Parse porcelain output - each line group starts with commit SHA
                    for line in result.stdout.split("\n"):
                        # Lines starting with a 40-char hex are commit SHAs
                        if len(line) >= 40 and all(c in "0123456789abcdef" for c in line[:40]):
                            commit_sha = line[:7]  # Short SHA
                            # Skip uncommitted changes (all zeros)
                            if commit_sha != "0000000":
                                commit_to_task[commit_sha] = task_name

            except Exception:
                continue

        return commit_to_task

    if not output_json:
        click.echo("Extracting commits from task files...")
    task_commits = extract_commits_from_tasks()

    # Extract reviewed files from task frontmatter
    reviewed_files = _extract_reviewed_files(tasks_dir)

    if not task_commits and not reviewed_files:
        click.echo("No commits found in task files.", err=True)
        click.echo("Task files must be committed to git for coverage tracking.", err=True)
        click.echo("Alternatively, add 'reviewed' entries to task frontmatter.", err=True)
        return

    if not output_json:
        click.echo(f"Found {len(task_commits)} commits in {len(set(task_commits.values()))} tasks")
        if reviewed_files:
            click.echo(f"Found {len(reviewed_files)} reviewed file(s) in task frontmatter")
        click.echo()

    # Get all files to analyze based on path glob
    scope_path = Path(path_glob).resolve()
    if scope_path.is_file():
        files_to_analyze = [scope_path]
    else:
        # Get all tracked files in scope
        try:
            result = subprocess.run(
                ["git", "ls-files", str(scope_path)],
                cwd=git_root,
                capture_output=True,
                text=True,
                check=True,
            )
            rel_paths = result.stdout.strip().split("\n")
            files_to_analyze = [git_root / p for p in rel_paths if p]
        except Exception as e:
            click.echo(f"Error listing files: {e}", err=True)
            return

    # Filter out task files themselves
    tasks_dir_resolved = tasks_dir.resolve()
    files_to_analyze = [
        f
        for f in files_to_analyze
        if f.exists() and not str(f.resolve()).startswith(str(tasks_dir_resolved))
    ]

    if not files_to_analyze:
        click.echo("No files to analyze in scope.", err=True)
        return

    if not output_json:
        click.echo(f"Analyzing {len(files_to_analyze)} file(s)...\n")

    # Analyze coverage per file
    file_coverage: dict[Path, dict[str, any]] = {}

    # Build a cache for reviewed file ancestry checks
    # Maps (file_path_rel, commit_sha) -> (is_covered, task_name)
    reviewed_coverage_cache: dict[tuple[str, str], tuple[bool, str | None]] = {}

    def check_reviewed_coverage(file_path_rel: str, commit_sha: str) -> tuple[bool, str | None]:
        """Check if a commit is covered by reviewed entries for this file.

        Uses git merge-base to check if the commit is an ancestor of any
        reviewed SHA for this file.

        Args:
            file_path_rel: Relative path to the file
            commit_sha: The commit SHA to check

        Returns:
            Tuple of (is_covered, task_name) where task_name is the covering task
        """
        cache_key = (file_path_rel, commit_sha)
        if cache_key in reviewed_coverage_cache:
            return reviewed_coverage_cache[cache_key]

        result = (False, None)

        if file_path_rel in reviewed_files:
            for reviewed_sha, task_name in reviewed_files[file_path_rel]:
                # Check if commit_sha is an ancestor of (or equal to) reviewed_sha
                if _is_ancestor_commit(commit_sha, reviewed_sha, git_root):
                    result = (True, task_name)
                    break

        reviewed_coverage_cache[cache_key] = result
        return result

    for file_path in files_to_analyze:
        try:
            # Get git blame for the file
            # Use -CCC to detect copies/renames across files
            result = subprocess.run(
                ["git", "blame", "-CCC", "--line-porcelain", str(file_path)],
                cwd=git_root,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                continue

            # Get relative path for reviewed file lookup
            try:
                file_path_rel = str(file_path.resolve().relative_to(git_root))
            except ValueError:
                file_path_rel = str(file_path)

            # Parse blame output
            lines_data = []
            current_commit = None
            current_commit_full = None

            for line in result.stdout.split("\n"):
                if line and line[0].isalnum() and len(line.split()) > 0:
                    # Commit SHA line
                    parts = line.split()
                    if len(parts[0]) == 40:  # Full SHA
                        current_commit_full = parts[0]
                        current_commit = parts[0][:7]  # Use short SHA
                elif line.startswith("\t") and current_commit:
                    # Actual code line
                    # First check traditional task commit coverage
                    task_name = task_commits.get(current_commit)
                    is_covered = task_name is not None

                    # If not covered by task commits, check reviewed files
                    if not is_covered and current_commit_full:
                        is_covered, task_name = check_reviewed_coverage(
                            file_path_rel, current_commit_full
                        )

                    lines_data.append(
                        {
                            "commit": current_commit,
                            "task": task_name,
                            "covered": is_covered,
                        }
                    )

            if lines_data:
                total_lines = len(lines_data)
                covered_lines = sum(1 for l in lines_data if l["covered"])
                coverage_pct = (covered_lines / total_lines * 100) if total_lines > 0 else 0

                file_coverage[file_path] = {
                    "total": total_lines,
                    "covered": covered_lines,
                    "percentage": coverage_pct,
                    "lines": lines_data,
                }

        except Exception as e:
            click.echo(f"Warning: Could not analyze {file_path}: {e}", err=True)
            continue

    # Calculate overall coverage
    total_lines = sum(fc["total"] for fc in file_coverage.values())
    total_covered = sum(fc["covered"] for fc in file_coverage.values())
    overall_pct = (total_covered / total_lines * 100) if total_lines > 0 else 0

    # If --short flag, just print the score and exit
    if short:
        click.echo(f"{overall_pct:.1f}% ({total_covered}/{total_lines} lines)")
        return

    # If --json flag, output JSON and exit
    if output_json:
        import json

        json_output = {
            "overall": {
                "percentage": round(overall_pct, 1),
                "covered": total_covered,
                "total": total_lines,
            },
            "files": {
                str(fp.relative_to(git_root)): {
                    "percentage": round(data["percentage"], 1),
                    "covered": data["covered"],
                    "total": data["total"],
                }
                for fp, data in file_coverage.items()
            },
        }
        click.echo(json.dumps(json_output))
        return

    # Display summary
    click.echo("=" * 60)
    click.echo(f"Overall Coverage: {overall_pct:.1f}% ({total_covered}/{total_lines} lines)")
    click.echo("=" * 60)
    click.echo()

    # Display per-file coverage
    click.echo("File Coverage:")
    click.echo("-" * 60)

    # Sort by coverage percentage (lowest first)
    sorted_files = sorted(file_coverage.items(), key=lambda x: x[1]["percentage"])

    for file_path, data in sorted_files:
        rel_path = file_path.relative_to(git_root)
        pct = data["percentage"]
        covered = data["covered"]
        total = data["total"]

        # Color code based on coverage
        if pct >= 80:
            status = "✓"
        elif pct >= 50:
            status = "○"
        else:
            status = "✗"

        click.echo(f"{status} {pct:5.1f}% ({covered:4}/{total:4}) {rel_path}")

    # Detailed report
    if detailed:
        click.echo()
        click.echo("=" * 60)
        click.echo("Detailed Line Coverage")
        click.echo("=" * 60)

        for file_path, data in sorted_files:
            rel_path = file_path.relative_to(git_root)
            click.echo()
            click.echo(f"File: {rel_path}")
            click.echo("-" * 60)

            try:
                file_lines = file_path.read_text(encoding="utf-8").split("\n")
                for i, (line_data, line_content) in enumerate(
                    zip(data["lines"], file_lines, strict=False), 1
                ):
                    if line_data["covered"]:
                        task_name = line_data["task"]
                        click.echo(f"{i:4} [COVERED by {task_name}] {line_content[:60]}")
                    else:
                        commit = line_data["commit"]
                        click.echo(f"{i:4} [NOT COVERED - {commit}] {line_content[:60]}")
            except Exception:
                click.echo("  (Could not read file contents)")

    click.echo()
    click.echo("=" * 60)


@task.command("stats")
def task_stats() -> None:
    """Show statistics for all tasks.

    Displays stats for each task sorted by date (most recent first):
    - Number of commits associated with the task
    - Number of lines covered by the task
    - Features (files) modified by the task

    Example:
        codebook task stats
    """
    import re

    cfg = CodeBookConfig.load()
    tasks_dir = Path(cfg.tasks_dir)

    if not tasks_dir.exists():
        click.echo("No tasks directory found.", err=True)
        return

    # Get git root
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        git_root = Path(result.stdout.strip())
    except Exception:
        click.echo("Error: Not in a git repository", err=True)
        return

    task_files = sorted(tasks_dir.glob("*.md"), reverse=True)  # Most recent first

    if not task_files:
        click.echo("No tasks found.", err=True)
        return

    click.echo("Task Statistics")
    click.echo("=" * 80)
    click.echo()

    for task_file in task_files:
        task_name = task_file.stem
        content = task_file.read_text(encoding="utf-8")

        # Parse task date from filename (YYYYMMDDHHMM format)
        task_date_str = None
        if len(task_name) >= 12 and task_name[:12].isdigit():
            date_part = task_name[:12]
            task_date_str = (
                f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} "
                f"{date_part[8:10]}:{date_part[10:12]}"
            )
            title_part = (
                task_name[13:] if len(task_name) > 13 and task_name[12] == "-" else task_name
            )
            # Parse timestamp for filtering commits
            try:
                from datetime import datetime

                datetime.strptime(date_part, "%Y%m%d%H%M").timestamp()
            except Exception:
                pass
        elif len(task_name) > 9 and task_name[8] == "-" and task_name[:8].isdigit():
            # Old format (YYYYMMDD-)
            date_part = task_name[:8]
            task_date_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
            title_part = task_name[9:]
            try:
                from datetime import datetime

                datetime.strptime(date_part, "%Y%m%d").timestamp()
            except Exception:
                pass
        else:
            title_part = task_name
            task_date_str = "Unknown date"

        # Extract file paths from diff headers
        # Format: "diff --git a/path/to/file b/path/to/file"
        file_paths = set()
        in_diff_block = False

        for line in content.split("\n"):
            # Check if we're entering a diff block
            if line.startswith("```diff"):
                in_diff_block = True
                continue
            # Check if we're exiting a diff block
            if line.startswith("```") and in_diff_block:
                in_diff_block = False
                continue

            if in_diff_block:
                # Extract file paths from diff headers
                if line.startswith("diff --git"):
                    match = re.match(r"^diff --git a/([^\s]+) b/([^\s]+)", line)
                    if match:
                        # Use the "b/" path (after changes)
                        file_path = match.group(2)
                        file_paths.add(file_path)

        # Get commits that touched the task file itself
        # These are the commits that implemented the task
        commits = set()
        commit_full_shas = set()

        try:
            # Get git log for the task file itself
            cmd = ["git", "log", "--format=%H", "--follow", "--", str(task_file)]
            result = subprocess.run(
                cmd,
                cwd=git_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    if line:
                        full_sha = line.strip()
                        commits.add(full_sha[:7])
                        commit_full_shas.add(full_sha)
        except Exception:
            pass

        # Count total lines changed
        total_lines_added = 0
        total_lines_removed = 0
        is_ongoing = len(commits) == 0

        if is_ongoing:
            # Task has no commits yet - show current diff to HEAD for all files
            # Get all uncommitted changes (not just the files mentioned in the task)
            try:
                # Get diff stats for all uncommitted changes
                result = subprocess.run(
                    ["git", "diff", "--numstat", "HEAD"],
                    cwd=git_root,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.strip().split("\n"):
                        if line:
                            parts = line.split("\t")
                            if len(parts) >= 3:
                                try:
                                    added = int(parts[0]) if parts[0] != "-" else 0
                                    removed = int(parts[1]) if parts[1] != "-" else 0
                                    file_path = parts[2]
                                    # Skip markdown files in .codebook directory
                                    if not (
                                        file_path.startswith(".codebook/")
                                        and file_path.endswith(".md")
                                    ):
                                        total_lines_added += added
                                        total_lines_removed += removed
                                except ValueError:
                                    pass
            except Exception:
                pass
        else:
            # Count lines from commits
            for commit_sha in commit_full_shas:
                try:
                    # Get the diff stats for this commit
                    result = subprocess.run(
                        ["git", "show", "--numstat", "--pretty=format:", commit_sha],
                        cwd=git_root,
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode == 0:
                        for line in result.stdout.strip().split("\n"):
                            if line:
                                parts = line.split("\t")
                                if len(parts) >= 2:
                                    try:
                                        added = int(parts[0]) if parts[0] != "-" else 0
                                        removed = int(parts[1]) if parts[1] != "-" else 0
                                        total_lines_added += added
                                        total_lines_removed += removed
                                    except ValueError:
                                        # Skip binary files or invalid lines
                                        pass
                except Exception:
                    continue

        # Display task stats
        status = " (ONGOING)" if is_ongoing else ""
        click.echo(f"[{task_date_str}] {title_part}{status}")
        click.echo(f"  Commits:  {len(commits)}")
        click.echo(f"  Lines:    +{total_lines_added} -{total_lines_removed}")
        click.echo(f"  Features: {len(file_paths)}")
        if file_paths:
            click.echo("  Files:")
            for fp in sorted(file_paths):
                click.echo(f"    - {fp}")
        click.echo()

    click.echo("=" * 80)


def _find_ongoing_task(tasks_dir: Path) -> Path | None:
    """Find the ongoing (most recent untracked/modified) task file.

    An ongoing task is one that has not been committed yet or has uncommitted changes.

    Args:
        tasks_dir: Path to the tasks directory

    Returns:
        Path to the ongoing task file, or None if not found
    """
    modified_tasks = _get_modified_task_files(tasks_dir)
    if modified_tasks:
        # Return the most recent (last in sorted list)
        return modified_tasks[-1]
    return None


def _add_reviewed_to_task(task_file: Path, file_sha: str) -> bool:
    """Add a reviewed entry to task frontmatter.

    Args:
        task_file: Path to the task file
        file_sha: The file:sha string to add (e.g., "path/to/file.py:abc123")

    Returns:
        True if successfully updated, False otherwise
    """
    import yaml

    content = task_file.read_text(encoding="utf-8")

    # Parse existing frontmatter
    frontmatter_match = re.match(r"^---\n(.*?)\n---\n?", content, re.DOTALL)

    if frontmatter_match:
        # Has existing frontmatter
        yaml_content = frontmatter_match.group(1)
        rest_of_content = content[frontmatter_match.end() :]

        try:
            data = yaml.safe_load(yaml_content) or {}
        except yaml.YAMLError:
            data = {}

        if not isinstance(data, dict):
            data = {}

        # Get or create reviewed list
        reviewed = data.get("reviewed", [])
        if isinstance(reviewed, str):
            reviewed = [reviewed]
        if not isinstance(reviewed, list):
            reviewed = []

        # Check if entry already exists
        if file_sha not in reviewed:
            reviewed.append(file_sha)

        data["reviewed"] = reviewed

        # Rebuild frontmatter
        new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False)
        new_content = f"---\n{new_yaml}---\n{rest_of_content}"

    else:
        # No existing frontmatter - add one
        new_frontmatter = f"---\nreviewed:\n  - {file_sha}\n---\n"
        new_content = new_frontmatter + content

    task_file.write_text(new_content, encoding="utf-8")
    return True


@task.command("mark-reviewed")
@click.argument("file_path_or_sha", type=str)
@click.option(
    "--task",
    "-t",
    "task_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to specific task file (defaults to ongoing task)",
)
def task_mark_reviewed(file_path_or_sha: str, task_path: Path | None) -> None:
    """Mark a file as reviewed in a task's frontmatter.

    FILE_PATH_OR_SHA can be either:
    - Just a file path (SHA will be auto-resolved to HEAD)
    - File path with SHA: path/to/file.md:sha

    By default, adds the reviewed entry to the ongoing task (most recent
    untracked or modified task file). Use --task to specify a different task.

    Example:
        codebook task mark-reviewed src/main.py
        codebook task mark-reviewed src/main.py:abc123def
        codebook task mark-reviewed src/main.py --task ./tasks/MY_TASK.md
    """
    cfg = CodeBookConfig.load()
    tasks_dir = Path(cfg.tasks_dir)

    # Parse input - check if SHA is provided
    if ":" in file_path_or_sha:
        file_path_part, sha_part = file_path_or_sha.rsplit(":", 1)
        if not file_path_part:
            click.echo("Error: Invalid format. Use 'path/to/file' or 'path/to/file:sha'", err=True)
            sys.exit(1)
    else:
        file_path_part = file_path_or_sha
        sha_part = "HEAD"

    # Resolve SHA
    try:
        result = subprocess.run(
            ["git", "rev-parse", sha_part],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            resolved_sha = result.stdout.strip()
        else:
            click.echo(f"Error: Could not resolve SHA '{sha_part}'", err=True)
            sys.exit(1)
    except Exception as e:
        click.echo(f"Error resolving SHA: {e}", err=True)
        sys.exit(1)

    file_sha = f"{file_path_part}:{resolved_sha}"

    # Find the task file
    if task_path:
        target_task = task_path
    else:
        target_task = _find_ongoing_task(tasks_dir)
        if not target_task:
            click.echo("Error: No ongoing task found.", err=True)
            click.echo(
                "Create a new task first with 'codebook task new' or specify --task", err=True
            )
            sys.exit(1)

    # Add reviewed entry
    try:
        if _add_reviewed_to_task(target_task, file_sha):
            click.echo(f"Added reviewed entry to {target_task}:")
            click.echo(f"  - {file_sha}")
        else:
            click.echo("Failed to update task file", err=True)
            sys.exit(1)
    except Exception as e:
        click.echo(f"Error updating task file: {e}", err=True)
        sys.exit(1)


# AI Helpers
SUPPORTED_AGENTS = ["claude", "codex", "gemini", "opencode", "kimi"]


@main.group()
def ai() -> None:
    """AI helpers for CodeBook tasks.

    Use AI agents to review and work on tasks.

    Example:
        codebook ai help
        codebook ai review claude ./codebook/tasks/202512281502-TITLE.md
    """
    pass


@ai.command("help")
def ai_help() -> None:
    """Show help for AI helpers.

    Lists available AI agents and how to use them.

    Example:
        codebook ai help
    """
    click.echo("CodeBook AI Helpers")
    click.echo("=" * 40)
    click.echo()
    click.echo("Available commands:")
    click.echo("  codebook ai help     Show this help message")
    click.echo("  codebook ai review   Review a task with an AI agent")
    click.echo()
    click.echo("Supported agents:")
    for agent in SUPPORTED_AGENTS:
        click.echo(f"  - {agent}")
    click.echo()
    click.echo("Usage:")
    click.echo("  codebook ai review [agent] [path] -- [agent_args]")
    click.echo()
    click.echo("When no path is provided, all modified and untracked markdown files")
    click.echo("in the tasks directory are reviewed.")
    click.echo()
    click.echo("Examples:")
    click.echo("  codebook ai review claude ./codebook/tasks/202512281502-TITLE.md")
    click.echo("  codebook ai review claude  # Reviews all modified/untracked task files")
    click.echo(
        "  codebook ai review gemini ./codebook/tasks/202512281502-TITLE.md -- --model gemini-pro"
    )
    click.echo()
    click.echo("The review prompt can be customized in codebook.yml under 'ai.review_prompt'.")


def _get_modified_task_files(tasks_dir: Path) -> list[Path]:
    """Get modified and untracked markdown files in the tasks directory.

    Uses git to find:
    - Modified files (staged and unstaged)
    - Untracked files

    Args:
        tasks_dir: Path to the tasks directory

    Returns:
        List of paths to modified/untracked markdown files
    """
    if not tasks_dir.exists():
        return []

    task_files: list[Path] = []

    try:
        # Get modified files (staged and unstaged)
        modified_result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD", "--", str(tasks_dir)],
            capture_output=True,
            text=True,
        )
        if modified_result.returncode == 0:
            for line in modified_result.stdout.strip().split("\n"):
                if line and line.endswith(".md"):
                    path = Path(line)
                    if path.exists():
                        task_files.append(path)

        # Get untracked files
        untracked_result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard", "--", str(tasks_dir)],
            capture_output=True,
            text=True,
        )
        if untracked_result.returncode == 0:
            for line in untracked_result.stdout.strip().split("\n"):
                if line and line.endswith(".md"):
                    path = Path(line)
                    if path.exists() and path not in task_files:
                        task_files.append(path)

    except FileNotFoundError:
        # Git not available, return empty list
        pass

    return sorted(task_files)


def _run_agent_review(
    ctx: click.Context,
    agent: str,
    path: Path,
    agent_args: tuple[str, ...],
    cfg: CodeBookConfig,
) -> int:
    """Run a single agent review on a task file.

    Args:
        ctx: Click context
        agent: Agent name
        path: Path to task file
        agent_args: Additional agent arguments
        cfg: CodeBook configuration

    Returns:
        Exit code from the agent
    """
    # Build the prompt by replacing [TASK_FILE] with the actual path
    prompt = cfg.ai.review_prompt.replace("[TASK_FILE]", str(path.resolve()))

    # Build the agent command
    agent_cmd = _build_agent_command(agent, prompt, agent_args)

    if agent_cmd is None:
        click.echo(f"Error: Agent '{agent}' is not properly configured", err=True)
        return 1

    click.echo(f"Starting {agent} to review {path}...")
    if ctx.obj.get("verbose"):
        click.echo(f"Command: {' '.join(agent_cmd)}")

    try:
        # Run the agent command
        # Security note: Using list format (not shell=True) protects against shell injection.
        # The agent name is constrained to SUPPORTED_AGENTS via click.Choice, and the prompt/args
        # come from user-controlled config and CLI input, which is expected behavior.
        result = subprocess.run(agent_cmd)
        return result.returncode
    except FileNotFoundError:
        click.echo(f"Error: Agent '{agent}' not found. Is it installed?", err=True)
        return 1
    except Exception as e:
        click.echo(f"Error running agent: {e}", err=True)
        return 1


@ai.command("review")
@click.argument("agent", type=click.Choice(SUPPORTED_AGENTS))
@click.argument(
    "path", type=click.Path(exists=True, dir_okay=False, path_type=Path), required=False
)
@click.argument("agent_args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def ai_review(
    ctx: click.Context, agent: str, path: Path | None, agent_args: tuple[str, ...]
) -> None:
    """Review a task with an AI agent.

    Starts the specified AI agent with a review prompt for the given task file.
    The prompt can be customized in codebook.yml under 'ai.review_prompt'.

    AGENT is one of: claude, codex, gemini, opencode, kimi

    PATH is the path to the task file to review. If not provided, all modified
    and untracked markdown files in the tasks directory will be reviewed.

    AGENT_ARGS are additional arguments passed to the agent command.
    Use -- to separate them from codebook arguments.

    Example:
        codebook ai review claude ./codebook/tasks/202512281502-TITLE.md
        codebook ai review claude  # Reviews all modified/untracked task files
        codebook ai review gemini ./codebook/tasks/202512281502-TITLE.md -- --model gemini-pro
    """
    # Load config for review prompt
    cfg = CodeBookConfig.load()

    # If no path provided, find all modified/untracked task files
    if path is None:
        tasks_dir = Path(cfg.tasks_dir)
        task_files = _get_modified_task_files(tasks_dir)

        if not task_files:
            click.echo(f"No modified or untracked markdown files found in {tasks_dir}")
            sys.exit(0)

        click.echo(f"Found {len(task_files)} task file(s) to review:")
        for f in task_files:
            click.echo(f"  - {f}")
        click.echo()

        # Review each file
        exit_code = 0
        for task_file in task_files:
            result = _run_agent_review(ctx, agent, task_file, agent_args, cfg)
            if result != 0:
                exit_code = result

        sys.exit(exit_code)
    else:
        # Single file review
        exit_code = _run_agent_review(ctx, agent, path, agent_args, cfg)
        sys.exit(exit_code)


# Agent command configurations: maps agent name to (executable, prompt_flag or None)
# If prompt_flag is None, the prompt is passed as a positional argument
AGENT_COMMANDS: dict[str, tuple[str, str | None]] = {
    "claude": ("claude", "--print"),  # claude [args] --print "prompt"
    "codex": ("codex", None),  # codex [args] "prompt"
    "gemini": ("gemini", "--prompt-interactive"),  # gemini [args] --prompt-interactive "prompt"
    "opencode": ("opencode", None),  # opencode [args] "prompt"
    "kimi": ("kimi", "--command"),  # kimi [args] --command "prompt"
}


def _build_agent_command(agent: str, prompt: str, agent_args: tuple[str, ...]) -> list[str] | None:
    """Build the command to run an AI agent.

    Args:
        agent: Name of the agent (claude, codex, gemini, opencode, kimi)
        prompt: The prompt to send to the agent
        agent_args: Additional arguments for the agent (inserted before prompt)

    Returns:
        Command as a list of strings, or None if agent not supported
    """
    if agent not in AGENT_COMMANDS:
        return None

    executable, prompt_flag = AGENT_COMMANDS[agent]
    args = list(agent_args)

    # Build command: executable [args] [prompt_flag] prompt
    if prompt_flag:
        return [executable, *args, prompt_flag, prompt]
    else:
        return [executable, *args, prompt]


if __name__ == "__main__":
    main()
