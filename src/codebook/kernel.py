"""Jupyter kernel manager for executing code in markdown files.

This module provides integration with Jupyter kernels to execute code blocks
embedded in markdown files and capture their output.
"""

import atexit
import queue
import re
from dataclasses import dataclass
from typing import Any

from jupyter_client import KernelManager

# Regex to match ANSI escape codes
ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")


@dataclass
class ExecutionResult:
    """Result of code execution.

    Attributes:
        output: The captured stdout/display output
        error: Any error message if execution failed
        success: Whether execution completed without errors
    """

    output: str
    error: str | None
    success: bool


class CodeBookKernel:
    """Manages a Jupyter kernel for code execution.

    Provides methods to execute code and capture output, with automatic
    kernel lifecycle management.
    """

    def __init__(self, kernel_name: str = "python3", timeout: float = 30.0, cwd: str | None = None):
        """Initialize the kernel manager.

        Args:
            kernel_name: The Jupyter kernel to use (default: python3)
            timeout: Timeout in seconds for code execution
            cwd: Working directory to add to sys.path (enables importing project modules)
        """
        self.kernel_name = kernel_name
        self.timeout = timeout
        self.cwd = cwd
        self._km: KernelManager | None = None
        self._kc: Any = None
        self._started = False

    def start(self) -> None:
        """Start the Jupyter kernel."""
        if self._started:
            return

        self._km = KernelManager(kernel_name=self.kernel_name)
        self._km.start_kernel()
        self._kc = self._km.client()
        self._kc.start_channels()
        self._kc.wait_for_ready(timeout=self.timeout)
        self._started = True

        # Add project directory to sys.path so users can import their modules
        if self.cwd:
            setup_code = f"import sys; sys.path.insert(0, {self.cwd!r})"
            self._kc.execute(setup_code)
            # Wait for the setup to complete
            while True:
                msg = self._kc.get_iopub_msg(timeout=self.timeout)
                if msg["header"]["msg_type"] == "status":
                    if msg["content"].get("execution_state") == "idle":
                        break

        # Register cleanup on exit
        atexit.register(self.stop)

    def stop(self) -> None:
        """Stop the Jupyter kernel."""
        if not self._started:
            return

        if self._kc:
            self._kc.stop_channels()
        if self._km:
            self._km.shutdown_kernel(now=True)

        self._km = None
        self._kc = None
        self._started = False

    def execute(self, code: str) -> ExecutionResult:
        """Execute code and return the result.

        Args:
            code: The code to execute

        Returns:
            ExecutionResult with output, error, and success status
        """
        if not self._started:
            self.start()

        # Execute the code
        msg_id = self._kc.execute(code)

        # Collect output
        outputs: list[str] = []
        error: str | None = None

        while True:
            try:
                msg = self._kc.get_iopub_msg(timeout=self.timeout)
            except queue.Empty:
                error = "Execution timed out"
                break

            msg_type = msg["header"]["msg_type"]
            content = msg["content"]

            # Check if this message is for our execution
            if msg.get("parent_header", {}).get("msg_id") != msg_id:
                continue

            if msg_type == "stream":
                # stdout/stderr output
                outputs.append(content["text"])
            elif msg_type == "execute_result":
                # Expression result
                data = content.get("data", {})
                if "text/plain" in data:
                    outputs.append(data["text/plain"])
            elif msg_type == "display_data":
                # Display output (e.g., from display())
                data = content.get("data", {})
                if "text/plain" in data:
                    outputs.append(data["text/plain"])
            elif msg_type == "error":
                # Execution error - strip ANSI escape codes from traceback
                traceback = content.get("traceback", [content.get("evalue", "Unknown error")])
                raw_error = "\n".join(traceback)
                error = ANSI_ESCAPE_PATTERN.sub("", raw_error)
                break
            elif msg_type == "status" and content.get("execution_state") == "idle":
                # Execution complete
                break

        output = "".join(outputs).rstrip()
        return ExecutionResult(
            output=output,
            error=error,
            success=error is None,
        )

    def __enter__(self) -> "CodeBookKernel":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.stop()
