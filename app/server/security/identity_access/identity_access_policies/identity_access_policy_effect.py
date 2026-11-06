from enum import Enum


class IdentityAccessPolicyEffect(str, Enum):
    """What a statement says when it applies to a request. There is deliberately no
    third value: a statement that does not apply says nothing at all, and that silence
    is what keeps the implicit deny — nothing granted it — distinct from a statement
    that forbids it outright."""

    ALLOW = "Allow"
    DENY = "Deny"
