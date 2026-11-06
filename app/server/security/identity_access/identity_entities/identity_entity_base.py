import re
from uuid import uuid4
from typing import Optional
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pydantic import BaseModel, Field, SecretStr, field_validator

from app.server.security.identity_access.identity_access_vrn import format_entity_vrn
from app.server.security.identity_access.identity_entities.identity_entity_type import IdentityEntityType
from app.server.security.identity_access.identity_access_roles.identity_access_role_type import IdentityAccessRoleType

NAME_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]{2,31}")


class IdentityEntityBase(BaseModel, ABC):
    """Abstract base for a principal — the 'who' of every request, the counterpart of an
    IAM user. An entity carries no permissions of its own. What it may do comes entirely
    from the role it assumes, and which roles it may assume is decided by those roles'
    trust policies, matched against the entity's VRN. That is why the kind is part of
    the VRN: it lets a trust policy say 'every admin' with a single pattern.

    Names are normalised to lower case and restricted to a conservative alphabet, so two
    accounts can never differ only in case or in a look-alike character. The password
    hash is a SecretStr, so it never appears in a repr, a log line or a dumped response;
    reading it takes an explicit get_secret_value(), which a persistence layer will have
    to call and nothing else should."""

    model_config = {"frozen": True}

    id: str = Field(
        default_factory = lambda: uuid4().hex,
        description = "Stable, random identifier of this entity. Used in its VRN instead of the "
            "name, so a name that is later freed and reused can never inherit a grant that "
            "was written for the entity that held it before."
    )
    type: IdentityEntityType = Field(
        description = "Kind of principal. Each concrete subclass locks it to a Literal, so a "
            "stored entity can be loaded back into the right class without isinstance checks."
    )
    name: str = Field(
        description = "Sign-in name, unique across all stored entities. Normalised to lower "
            "case; 3-32 characters of a-z, 0-9, '.', '_' or '-', starting with a letter or digit."
    )
    password_hash: Optional[SecretStr] = Field(
        default = None,
        description = "Self-describing scrypt hash of the entity's password, as produced by "
            "AuthenticationPasswordHasher. Never the password itself. Narrowed per kind: "
            "required for admins and users, impossible for guests."
    )
    created_at: datetime = Field(
        default_factory = lambda: datetime.now(timezone.utc),
        description = "When the entity was created, in UTC."
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, name: str) -> str:
        normalised = name.strip().lower()

        if not NAME_PATTERN.fullmatch(normalised):
            raise ValueError(
                "A name is 3-32 characters of a-z, 0-9, '.', '_' or '-', starting with a "
                "letter or digit."
            )
        return normalised

    @property
    def vrn(self) -> str:
        return format_entity_vrn(self.type, self.id)

    @property
    @abstractmethod
    def default_role(self) -> IdentityAccessRoleType:
        raise NotImplementedError("Must be implemented")
