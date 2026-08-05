"""
Auth Domain Exceptions.
"""


class InvalidCredentialsException(Exception):
    """Raised when authentication fails due to invalid credentials."""
    pass


class TokenExpiredException(Exception):
    """Raised when JWT token has expired."""
    pass
