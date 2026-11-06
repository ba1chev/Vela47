from typing import Literal, Self
from pydantic import model_validator

from app.server.security.identity_access.identity_access_request import IdentityAccessRequest
from app.server.security.identity_access.identity_access_policies.identity_access_policy_type import IdentityAccessPolicyType
from app.server.security.identity_access.identity_access_policies.identity_access_policy_statement import IdentityAccessPolicyStatement
from app.server.security.identity_access.identity_access_policies.identity_access_resource_policy.identity_access_resource_policy_base import IdentityAccessResourcePolicyBase


class IdentityAccessResourcePolicy(IdentityAccessResourcePolicyBase):
    """A resource-based policy: attached to one resource, it says who may do what to it.
    It is how access crosses from one identity to another. A role can only ever reach
    what its own statements grant — typically the caller's own resources — so letting
    someone else in is something the resource has to grant, not something the other
    person's role can claim.

    Its verdict is unioned with the caller's permission policies, as AWS does within a
    single account: either one may allow, and an explicit deny in either one wins. It is
    found by the exact VRN it is attached to, and its statements' resource patterns are
    then matched against the request like any other statement's."""

    type: Literal[IdentityAccessPolicyType.RESOURCE] = IdentityAccessPolicyType.RESOURCE

    @model_validator(mode = "after")
    def validate_resources(self) -> Self:
        for current_statement in self.statements:
            if not current_statement.resources:
                raise ValueError(
                    f"Resource policy '{self.name}' has a statement without resources, "
                    f"which would cover nothing."
                )
        return self

    def covers(self, statement: IdentityAccessPolicyStatement,
        request: IdentityAccessRequest) -> bool:
        return (
            statement.matches_principal(request.principals)
            and statement.matches_action(request.action)
            and statement.matches_resource(request.resource, request.variables)
        )
