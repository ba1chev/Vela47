from enum import Enum


class IdentityEntityType(str, Enum):
    """Enumerates the kinds of principal that can make a request — who is asking, as
    opposed to what they are acting as. The kinds differ in how they prove it: admins
    and users sign in with a password and are stored, while guests are issued on
    demand, hold no credential and exist only inside their session token.

    The value is part of every entity's VRN, which is what lets a trust policy name a
    whole kind at once — vrn:iam::entity/admin/* — instead of listing people."""

    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
