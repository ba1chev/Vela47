from typing import Optional
from pydantic import BaseModel, Field

from app.server.security.identity_access.identity_access_roles.identity_access_role_type import IdentityAccessRoleType


class SignInRequest(BaseModel):
    """The body of a password sign-in. role is optional: left out, the entity acts as its
    default role; given, it has to be a role whose trust policy names that entity — which
    is how an admin opens an everyday session as the user role."""

    name: str = Field(
        min_length = 1,
        max_length = 64,
        description = "The entity's sign-in name. Matched case-insensitively, since names are "
            "stored in lower case."
    )
    password: str = Field(
        min_length = 1,
        max_length = 1024,
        description = "The entity's password. Checked against its stored hash, and never stored "
            "or logged itself."
    )
    role: Optional[IdentityAccessRoleType] = Field(
        default = None,
        description = "The role to act as. None means the entity's default role — admin for an "
            "admin, user for a user."
    )
