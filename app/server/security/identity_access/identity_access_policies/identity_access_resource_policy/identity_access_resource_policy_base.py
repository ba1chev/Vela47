from typing import Self
from pydantic import model_validator

from app.server.security.identity_access.identity_access_policies.identity_access_policy_base import IdentityAccessPolicyBase


class IdentityAccessResourcePolicyBase(IdentityAccessPolicyBase):
    """Abstract base for policies attached to something other than an identity — and
    which, for exactly that reason, must say who they apply to. Every statement has to
    name its principals; unlike a permission policy there is no role holder to fall back
    on, so a statement without principals is refused.

    A principal pattern is matched against every identity the caller presents: the
    entity it is and, once it holds one, the role it acts through. A statement can
    therefore grant to one person whichever role they currently hold —
    vrn:iam::entity/user/9f2c… — or to everyone acting as a role — vrn:iam::role/admin.

    Trust policies inherit from this because, as in AWS, a trust policy is the
    resource-based policy of a role."""

    @model_validator(mode = "after")
    def validate_principals(self) -> Self:
        for current_statement in self.statements:
            if not current_statement.principals:
                raise ValueError(
                    f"Policy '{self.name}' has a statement without principals — a policy not "
                    f"attached to an identity has to say who it applies to."
                )
        return self
