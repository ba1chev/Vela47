from pydantic import BaseModel, Field

from app.server.security.identity_access.identity_entities.identity_entity_type import IdentityEntityType


class CreateEntityRequest(BaseModel):
    """The body of an admin creating an account. The rules for names and passwords are
    not repeated here — the entity and the password hasher own them and enforce them at
    creation — so this only carries what the admin asked for."""

    type: IdentityEntityType = Field(
        description = "Kind of entity to create — 'admin' or 'user'. Guests are issued on demand "
            "and cannot be created."
    )
    name: str = Field(
        max_length = 64,
        description = "Sign-in name of the new entity. Normalised to lower case."
    )
    password: str = Field(
        max_length = 1024,
        description = "Initial password of the new entity, at least 12 characters long."
    )
