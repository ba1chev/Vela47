from typing import Literal
from pydantic import Field, SecretStr

from app.server.security.identity_access.identity_entities.identity_entity_base import IdentityEntityBase
from app.server.security.identity_access.identity_entities.identity_entity_type import IdentityEntityType
from app.server.security.identity_access.identity_access_roles.identity_access_role_type import IdentityAccessRoleType


class IdentityEntityUser(IdentityEntityBase):
    """A person with an account. Signs in with a password and acts as the user role.
    Users are created by an admin rather than by signing themselves up — the same
    stance as IAM, where an identity exists because someone with the authority to grant
    one decided it should."""

    type: Literal[IdentityEntityType.USER] = IdentityEntityType.USER
    password_hash: SecretStr = Field(
        description = "Self-describing scrypt hash of the user's password. Required: a user "
            "signs in with a password and has no other way to prove who they are."
    )

    @property
    def default_role(self) -> IdentityAccessRoleType:
        return IdentityAccessRoleType.USER
