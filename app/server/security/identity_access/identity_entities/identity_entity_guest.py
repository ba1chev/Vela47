from typing import Literal
from pydantic import Field

from app.server.security import IdentityEntityBase
from app.server.security import IdentityEntityType
from app.server.security import IdentityAccessRoleType


class IdentityEntityGuest(IdentityEntityBase):
    """An anonymous visitor — the counterpart of an unauthenticated Cognito identity. A
    guest proves nothing, so there is nothing about it worth storing: it is minted on
    request, known only by a random id, and exists solely inside its session token. That
    is what lets every visitor have an identity without the store growing by one entry
    per page load.

    The password field is narrowed to None, so a guest cannot carry a credential and can
    never come in through the password sign-in, even by accident."""

    type: Literal[IdentityEntityType.GUEST] = IdentityEntityType.GUEST
    name: str = Field(
        default = "guest",
        description = "Display name shared by every guest. Guests are never looked up by name, "
            "so it need not be unique."
    )
    password_hash: None = Field(
        default = None,
        description = "Always None — a guest has no credential to hold."
    )

    @property
    def default_role(self) -> IdentityAccessRoleType:
        return IdentityAccessRoleType.GUEST
