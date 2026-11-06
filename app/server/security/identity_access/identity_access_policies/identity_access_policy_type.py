from enum import Enum


class IdentityAccessPolicyType(str, Enum):
    """Enumerates the kinds of policy document, which differ by where each one is
    attached and therefore by what it has to name. A permission policy is attached to a
    role, so its principal is whoever holds the role and is never written. A resource
    policy is attached to a resource and must say who it grants to. A trust policy is
    attached to a role as well, but answers a different question — not what the role
    may do, but who may become it.

    Values are strings so a document serialises to readable JSON, which is the form it
    takes once policies are stored rather than defined in code."""

    PERMISSION = "permission"
    RESOURCE = "resource"
    TRUST = "trust"
