from typing import Self
from pydantic import model_validator

from app.server.security.identity_access.identity_access_action import IdentityAccessAction
from app.server.security.identity_access.identity_access_policies.identity_access_policy_utils import matches_pattern
from app.server.security.identity_access.identity_access_policies.identity_access_resource_policy.identity_access_resource_policy_base import IdentityAccessResourcePolicyBase


class IdentityAccessTrustPolicyBase(IdentityAccessResourcePolicyBase):
    """Abstract base for trust policies — in AWS terms the resource-based policy of a
    role, where the resource is the role itself and the only thing that can be asked of
    it is to be assumed. A trust policy decides who may act through a role, which is a
    separate question from what the role may do: the admin role's permission policy
    allows everything, and its trust policy is the only thing that keeps a user from
    claiming it.

    The role is implied, so statements may not name resources. And since assuming is
    the only action there is, every action pattern has to match iam:AssumeRole — a
    statement granting anything else cannot do what its author meant, and in a trust
    policy that kind of mistake decides who can become an administrator."""

    @model_validator(mode = "after")
    def validate_trust(self) -> Self:
        for current_statement in self.statements:
            if current_statement.resources:
                raise ValueError(
                    f"Trust policy '{self.name}' names resources — its resource is always "
                    f"the role it is attached to."
                )

            for current_action in current_statement.actions:
                if not matches_pattern(
                    current_action,
                    IdentityAccessAction.IAM_ASSUME_ROLE.value,
                    case_sensitive = False
                ):
                    raise ValueError(
                        f"Trust policy '{self.name}' grants '{current_action}', but the only "
                        f"action a trust policy governs is "
                        f"{IdentityAccessAction.IAM_ASSUME_ROLE.value}."
                    )
        return self
