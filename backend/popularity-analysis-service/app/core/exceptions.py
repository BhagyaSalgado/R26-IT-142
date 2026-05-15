class AppError(Exception):
    """Base application exception."""


class InvalidYouTubeUrlError(AppError):
    """Raised when a YouTube URL or video id cannot be parsed."""


class ExternalServiceError(AppError):
    """Raised when an external service such as YouTube API fails."""


class EntityNotFoundError(AppError):
    """Raised when an entity does not exist in the repository."""
