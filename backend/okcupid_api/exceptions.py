"""Custom exceptions for OkCupid API client."""


class OkCupidAPIError(Exception):
    """Base exception for API errors."""
    pass


class OkCupidAuthError(OkCupidAPIError):
    """Authentication or session invalid."""
    pass


class OkCupidRateLimitError(OkCupidAPIError):
    """Rate limited by server."""
    pass


class OkCupidNotFoundError(OkCupidAPIError):
    """Resource (e.g. profile) not found."""
    pass
