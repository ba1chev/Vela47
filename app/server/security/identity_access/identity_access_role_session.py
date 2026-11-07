from uuid import uuid4
from datetime import datetime
from pydantic import BaseModel, Field

from app.server.security import format_role_vrn
from app.server.security import format_entity_vrn
from app.server.security import IdentityEntityType
from app.server.security import IdentityAccessRoleType


class IdentityAccessRoleSession(BaseModel):
    """An entity acting through a role for a bounded time — what AWS STS hands back from
    AssumeRole, and exactly what a session token carries. Authentication produces one,
    the token codec serialises it, and authorization evaluates every request against it;
    nothing past sign-in ever sees a credential, only this.

    It names the role instead of copying the role's policies, so a change to what a role
    may do reaches sessions already issued rather than waiting for them to expire. It
    names the entity too, because a resource policy may grant to one specific entity
    whichever role that entity happens to be acting through.

    Called a role session rather than a session on purpose: the chat sessions the server
    is about to gain are a different thing entirely, and are owned by entities."""

    model_config = {"frozen": True}

    id: str = Field(
        default_factory = lambda: uuid4().hex,
        description = "Unique id of this session, carried as the token's jti claim. Lets one "
            "issued token be told apart from another for the same entity and role."
    )
    entity_id: str = Field(
        description = "Id of the entity acting. For admins and users it names a stored entity; "
            "for a guest it is the only place the guest's identity exists at all."
    )
    entity_type: IdentityEntityType = Field(
        description = "Kind of the acting entity. Part of the entity's VRN, which is what trust "
            "and resource policies match principals against."
    )
    role_type: IdentityAccessRoleType = Field(
        description = "The role the entity assumed. Authorization looks the role up by this "
            "value on every request, so the role's current policies always apply."
    )
    issued_at: datetime = Field(
        description = "When the role was assumed, in UTC and whole seconds — the precision a "
            "JWT carries, so a session reads the same before and after a round trip."
    )
    expires_at: datetime = Field(
        description = "When the session stops being accepted, in UTC. Set from the role's "
            "maximum session length at the moment the role was assumed."
    )

    @property
    def entity_vrn(self) -> str:
        return format_entity_vrn(self.entity_type, self.entity_id)

    @property
    def role_vrn(self) -> str:
        return format_role_vrn(self.role_type)

    @property
    def principals(self) -> list[str]:
        return [self.entity_vrn, self.role_vrn]

    @property
    def variables(self) -> dict[str, str]:
        return {
            "principal.id": self.entity_id,
            "principal.type": self.entity_type.value,
            "principal.role": self.role_type.value
        }
