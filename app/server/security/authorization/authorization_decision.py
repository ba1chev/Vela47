from enum import Enum


class AuthorizationDecision(str, Enum):
    """The three outcomes of evaluating a request against every applicable policy, named
    as AWS names them. The two kinds of denial are kept apart because they call for
    different fixes: an implicit deny means nothing granted the action, so the remedy is
    a policy that allows it; an explicit deny means a statement forbade it, and no allow
    anywhere can override that."""

    ALLOW = "allow"
    EXPLICIT_DENY = "explicit_deny"
    IMPLICIT_DENY = "implicit_deny"
