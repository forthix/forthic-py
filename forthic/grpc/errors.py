"""
Custom error classes that preserve context across runtime boundaries
"""
from typing import Any


class RemoteErrorInfo:
    """Error information from a remote runtime"""

    def __init__(
        self,
        message: str,
        runtime: str,
        stack_trace: list[str],
        error_type: str,
        word_location: str | None = None,
        module_name: str | None = None,
        context: dict[str, str] | None = None,
    ):
        self.message = message
        self.runtime = runtime
        self.stack_trace = stack_trace
        self.error_type = error_type
        self.word_location = word_location
        self.module_name = module_name
        self.context = context or {}


class RemoteRuntimeError(Exception):
    """
    Custom error class for errors that occur in remote runtimes
    Preserves stack trace and context from the remote runtime
    """

    def __init__(self, error_info: RemoteErrorInfo):
        # Build a rich error message
        message = f"Error in {error_info.runtime} runtime: {error_info.message}"

        if error_info.module_name:
            message += f"\n  Module: {error_info.module_name}"

        if error_info.word_location:
            message += f"\n  Location: {error_info.word_location}"

        if error_info.context:
            message += "\n  Context:"
            for key, value in error_info.context.items():
                message += f"\n    {key}: {value}"

        super().__init__(message)

        self.runtime = error_info.runtime
        self.remote_stack_trace = error_info.stack_trace
        self.error_type = error_info.error_type
        self.word_location = error_info.word_location
        self.module_name = error_info.module_name
        self.context = error_info.context

    def get_full_stack_trace(self) -> str:
        """Get the full stack trace including both local and remote context"""
        import traceback

        result = f"{self.__class__.__name__}: {str(self)}\n"

        # Add local Python stack
        result += "\nLocal stack (Python):\n"
        result += "".join(traceback.format_tb(self.__traceback__))

        # Add remote stack trace
        if self.remote_stack_trace:
            result += f"\n\nRemote stack ({self.runtime}):\n"
            result += "\n".join(self.remote_stack_trace)

        return result

    def get_error_report(self) -> str:
        """Get a formatted error report with all available context"""
        report = "=" * 80 + "\n"
        report += "REMOTE RUNTIME ERROR\n"
        report += "=" * 80 + "\n\n"

        report += f"Runtime: {self.runtime}\n"
        report += f"Error Type: {self.error_type}\n"
        report += f"Message: {self.args[0] if self.args else 'Unknown error'}\n"

        if self.module_name:
            report += f"Module: {self.module_name}\n"

        if self.word_location:
            report += f"Location: {self.word_location}\n"

        if self.context:
            report += "\nContext:\n"
            for key, value in self.context.items():
                report += f"  {key}: {value}\n"

        report += "\n" + "-" * 80 + "\n"
        report += "Stack Trace:\n"
        report += "-" * 80 + "\n"

        if self.remote_stack_trace:
            report += "\n".join(self.remote_stack_trace)

        report += "\n" + "=" * 80 + "\n"

        return report


def parse_error_info(error_info: Any) -> RemoteErrorInfo:
    """Parse ErrorInfo from protobuf response into RemoteErrorInfo"""
    return RemoteErrorInfo(
        message=error_info.message or "Unknown error",
        runtime=error_info.runtime or "unknown",
        stack_trace=list(error_info.stack_trace) if error_info.stack_trace else [],
        error_type=error_info.error_type or "Error",
        word_location=error_info.word_location if error_info.word_location else None,
        module_name=error_info.module_name if error_info.module_name else None,
        context=dict(error_info.context) if error_info.context else {},
    )
