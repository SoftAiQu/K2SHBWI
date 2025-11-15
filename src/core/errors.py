"""Common error types for K2SHBWI."""

class CompressionError(Exception):
    """Raised when compression or decompression fails."""
    pass

class ValidationError(Exception):
    """Raised when data validation fails."""
    pass

class FormatError(Exception):
    """Raised when format specification is violated."""
    pass