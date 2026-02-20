"""Custom exceptions for the UDM Pro MCP server."""


class UDMError(Exception):
    """Base exception for UDM Pro operations."""


class AuthenticationError(UDMError):
    """Failed to authenticate with the UDM Pro."""


class ConfigError(UDMError):
    """Invalid or missing configuration."""


class APIError(UDMError):
    """UDM Pro API returned an error."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class DeviceNotFoundError(UDMError):
    """Requested device was not found."""


class ClientNotFoundError(UDMError):
    """Requested client was not found."""
