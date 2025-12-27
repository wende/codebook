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

import logging
import os
import signal
import subprocess
import sys
from pathlib import Path

import click

from .client import CodeBookClient
from .renderer import CodeBookRenderer
from .watcher import CodeBookWatcher
from .differ import CodeBookDiffer
from .kernel import CodeBookKernel
from .cicada import CicadaClient
from .config import CodeBookConfig


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


@click.group()
@click.version_option(version="0.1.0", prog_name="codebook")
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
        kernel = CodeBookKernel()
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
        kernel = CodeBookKernel()
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
            click.echo(f"Starting Cicada on port {cfg.cicada.port}...")
            proc = subprocess.Popen(
                ["cicada", "serve", "--port", str(cfg.cicada.port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            processes.append(proc)

        # Start mock backend if configured
        if cfg.backend.start:
            click.echo(f"Starting backend on port {cfg.backend.port}...")
            mock_server = Path(__file__).parent.parent.parent.parent / "examples" / "mock_server.py"
            proc = subprocess.Popen(
                ["python", str(mock_server), "--port", str(cfg.backend.port)],
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
        if cfg.exec:
            click.echo("Starting Jupyter kernel...")
            kernel = CodeBookKernel()
            kernel.start()

        # Create Cicada client if enabled
        cicada = None
        if cfg.cicada.enabled:
            click.echo(f"Connecting to Cicada at {cfg.cicada.url}...")
            cicada = CicadaClient(base_url=cfg.cicada.url)

        try:
            renderer = CodeBookRenderer(client, kernel=kernel, cicada=cicada)
            directory = Path(cfg.watch_dir)

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
        watch_dir=".",
        exec=True,
        recursive=True,
        backend=CodeBookConfig._from_dict({}).backend,
        cicada=CodeBookConfig._from_dict({"cicada": {"enabled": True, "start": True}}).cicada,
    )
    config.backend.start = True
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


@task.command("new")
@click.argument("title", type=str)
@click.argument("scope", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--all",
    "include_all",
    is_flag=True,
    help="Include all files, not just modified ones",
)
@click.pass_context
def task_new(ctx: click.Context, title: str, scope: Path, include_all: bool) -> None:
    """Create a new task capturing modified files and their diffs.

    Creates a task file at .codebook/tasks/TITLE.md containing
    the original content and git diff for each MODIFIED file in scope.

    By default, only includes files with uncommitted changes.
    Use --all to include all files regardless of git status.

    Example:
        codebook task new "Feature Documentation" ./docs
        codebook task new "API Update" ./README.md
        codebook task new "Full Snapshot" ./docs --all
    """
    import re

    # Convert title to UPPER_SNAKE_CASE
    task_name = re.sub(r"[^\w\s]", "", title)
    task_name = re.sub(r"\s+", "_", task_name).upper()

    # Create tasks directory
    tasks_dir = Path(".codebook/tasks")
    tasks_dir.mkdir(parents=True, exist_ok=True)

    task_file = tasks_dir / f"{task_name}.md"

    # Get modified files from git
    def get_modified_files(scope_path: Path) -> set[Path]:
        """Get list of modified files (staged + unstaged) in scope."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", str(scope_path)],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return set()
            modified = set()
            for line in result.stdout.split("\n"):
                if line and len(line) >= 3:
                    # Format: "XY filename" where XY is 2-char status + space
                    file_path = line[3:]
                    # Handle renamed files: "R  old -> new"
                    if " -> " in file_path:
                        file_path = file_path.split(" -> ")[1]
                    # Resolve to absolute path for comparison
                    modified.add(Path(file_path).resolve())
            return modified
        except Exception:
            return set()

    # Get raw git diff for a file
    def get_git_diff(file_path: Path) -> str | None:
        """Get raw git diff for a file."""
        try:
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

    # Collect files to process
    if scope.is_file():
        candidates = [scope]
    else:
        candidates = sorted(scope.glob("**/*.md"))

    # Filter to only modified files unless --all
    if include_all:
        files = candidates
    else:
        modified = get_modified_files(scope)
        files = [f for f in candidates if f.resolve() in modified]

    if not files:
        click.echo(f"No modified markdown files found in {scope}", err=True)
        click.echo("Use --all to include all files regardless of git status", err=True)
        return

    # Build task content
    lines = [f"# {title}\n\n"]
    file_count = 0

    for file_path in files:
        if not file_path.is_file():
            continue

        # Read current content
        try:
            current_content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            click.echo(f"Error reading {file_path}: {e}", err=True)
            continue

        # Get raw git diff
        diff_output = get_git_diff(file_path)

        file_count += 1
        lines.append(f"## {file_count}. {file_path}\n\n")

        # Show before content
        lines.append("### Before\n\n")
        lines.append("```markdown\n")
        lines.append(current_content)
        if not current_content.endswith("\n"):
            lines.append("\n")
        lines.append("```\n\n")

        # Show diff if any
        if diff_output:
            lines.append("### Diff\n\n")
            lines.append("```diff\n")
            lines.append(diff_output)
            if not diff_output.endswith("\n"):
                lines.append("\n")
            lines.append("```\n\n")

        lines.append("---\n\n")

    if file_count == 0:
        click.echo(f"No modified markdown files found in {scope}", err=True)
        click.echo("Use --all to include all files regardless of git status", err=True)
        return

    # Write task file
    task_file.write_text("".join(lines), encoding="utf-8")
    click.echo(f"Created task: {task_file} ({file_count} file(s))")


if __name__ == "__main__":
    main()
