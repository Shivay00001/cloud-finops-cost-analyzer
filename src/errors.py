"""Structured error types for the FinOps cost analyzer.

All user-facing errors are raised as FinopsError subclasses and rendered
by the CLI as a single clean line on stderr with a non-zero exit code.
Tracebacks are NEVER shown to end users.
"""

EXIT_INPUT = 1       # bad CLI usage / missing file / unreadable input
EXIT_VALIDATION = 2  # CSV schema / data validation failure
EXIT_UNEXPECTED = 3  # anything else (wrapped, no traceback)


class FinopsError(Exception):
    """Base class: message is safe to show to the end user."""

    exit_code = EXIT_UNEXPECTED

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InputError(FinopsError):
    """Bad CLI usage, missing/unreadable input file."""
    exit_code = EXIT_INPUT


class ValidationError(FinopsError):
    """CSV schema or data validation failure."""
    exit_code = EXIT_VALIDATION


def render_error(exc: BaseException) -> str:
    """One-line structured error string for stderr."""
    if isinstance(exc, FinopsError):
        return f"ERROR [{exc.__class__.__name__}]: {exc.message}"
    # Unexpected: deliberately no detail, no traceback.
    return "ERROR [UnexpectedError]: analysis failed unexpectedly (no data written)."
