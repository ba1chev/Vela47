from typing import Literal
from pydantic import Field, SecretStr

from app.server.security.identity_access.identity_entities.identity_entity_base import IdentityEntityBase
from app.server.security.identity_access.identity_entities.identity_entity_type import IdentityEntityType
from app.server.security.identity_access.identity_access_roles.identity_access_role_type import IdentityAccessRoleType


class IdentityEntityAdmin(IdentityEntityBase):
    """A person trusted with the admin role. Being an admin entity grants nothing by
    itself — it is what the admin role's trust policy names, and the admin still has to
    assume that role to act on it. Signing in assumes it by default; asking for the user
    role instead gives the same person an everyday session that cannot touch identity,
    which is the least-privilege habit AWS recommends for its own administrators."""

    type: Literal[IdentityEntityType.ADMIN] = IdentityEntityType.ADMIN
    password_hash: SecretStr = Field(
        description = "Self-describing scrypt hash of the admin's password. Required: an admin "
            "signs in with a password and has no other way to prove who they are."
    )

    @property
    def default_role(self) -> IdentityAccessRoleType:
        return IdentityAccessRoleType.ADMIN
