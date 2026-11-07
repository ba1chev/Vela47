from typing import Literal, Self
from pydantic import model_validator

from app.server.security import IdentityAccessRequest
from app.server.security import IdentityAccessPolicyBase
from app.server.security import IdentityAccessPolicyType
from app.server.security import IdentityAccessPolicyStatement


class IdentityAccessPermissionPolicy(IdentityAccessPolicyBase):
    """An identity-based policy: attached to a role, it states what anyone acting through
    that role may do. The principal is whoever holds the role, so naming one in a
    statement would be redundant at best and misleading at worst — such statements are
    refused rather than silently ignored.

    Every statement has to name resources. One without them would cover nothing, and a
    grant that covers nothing is almost always a mistake nobody notices until the
    permission it was meant to give turns out to be missing."""

    type: Literal[IdentityAccessPolicyType.PERMISSION] = IdentityAccessPolicyType.PERMISSION

    @model_validator(mode = "after")
    def validate_statements(self) -> Self:
        for current_statement in self.statements:
            if current_statement.principals:
                raise ValueError(
                    f"Permission policy '{self.name}' names principals — its principal is "
                    f"whoever holds the role it is attached to."
                )
            if not current_statement.resources:
                raise ValueError(
                    f"Permission policy '{self.name}' has a statement without resources, "
                    f"which would cover nothing."
                )
        return self

    def covers(self, statement: IdentityAccessPolicyStatement,
        request: IdentityAccessRequest) -> bool:
        return (
            statement.matches_action(request.action)
            and statement.matches_resource(request.resource, request.variables)
        )
