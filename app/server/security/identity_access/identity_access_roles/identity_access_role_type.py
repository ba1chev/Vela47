from enum import Enum


class IdentityAccessRoleType(str, Enum):
    """Enumerates the built-in roles. A role is what a principal acts as, not who it is —
    the same admin entity can act as the admin role or, for everyday work, as the user
    role — which is why this enum exists alongside IdentityEntityType even though their
    members share names. The value is part of the role's VRN and is what a session token
    carries in its role claim."""

    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
