class AutoQuantError(Exception):
    """Base exception for all Auto-Quant errors."""
    pass

class LLMConnectionError(AutoQuantError):
    """Raised when NVIDIA NIM API fails."""
    pass

class SandboxExecutionError(AutoQuantError):
    """Raised when the Docker sandbox fails or times out."""
    pass

class OutputValidationError(AutoQuantError):
    """Raised when an agent produces malformed Pydantic output."""
    pass

class ToolExecutionError(AutoQuantError):
    """Raised when an external tool (e.g., SEC EDGAR, Tavily) fails."""
    pass