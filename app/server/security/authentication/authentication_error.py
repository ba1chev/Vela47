class AuthenticationError(Exception):
    """Raised when the caller's identity cannot be established — no token, a forged or
    expired one, or credentials that do not match. The server answers it with 401, the
    signal for a client to sign in again, as opposed to the 403 of AuthorizationError,
    which means signing in again would change nothing.

    Its messages are written to be safe to show the caller: they say that sign-in
    failed, never which half of the credentials was wrong, so the error cannot be used
    to find out which names exist."""
