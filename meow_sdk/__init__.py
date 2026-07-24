"""meow meow scratch Python SDK — create, read, and manage API data programmatically."""

from .client import Meow
from .exceptions import AuthError, MeowError, NotFoundError, RateLimitError, ValidationError

__version__ = "0.7.0"
__all__ = ["Meow", "MeowError", "AuthError", "NotFoundError", "ValidationError", "RateLimitError"]
