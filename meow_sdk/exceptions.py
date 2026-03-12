class MeowError(Exception):
    """Something went wrong talking to the meow meow scratch API."""

    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthError(MeowError):
    """API key is missing, invalid, or doesn't have the right permissions."""


class NotFoundError(MeowError):
    """The app, endpoint, or record you asked for doesn't exist."""


class ValidationError(MeowError):
    """The data you sent isn't right — check the error message for details."""


class RateLimitError(MeowError):
    """Too many requests — slow down and try again in a moment."""
