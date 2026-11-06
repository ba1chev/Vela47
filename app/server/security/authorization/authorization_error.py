class AuthorizationError(Exception):
    """Raised when a caller whose identity is known asks for something it may not do —
    whether an action its role does not grant, or a role whose trust policy does not
    name it. The server answers it with 403, kept apart from the 401 of
    AuthenticationError so a client can tell 'sign in' from 'you may not', which call
    for opposite reactions."""
