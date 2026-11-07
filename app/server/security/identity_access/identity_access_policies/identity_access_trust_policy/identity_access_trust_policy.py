from typing import Literal

from app.server.security import IdentityAccessRequest
from app.server.security import IdentityAccessPolicyType
from app.server.security import IdentityAccessPolicyStatement
from app.server.security import IdentityAccessTrustPolicyBase


class IdentityAccessTrustPolicy(IdentityAccessTrustPolicyBase):
    """The trust policy a role carries, evaluated each time an entity asks to assume
    that role. Only principals and actions are compared — the resource is always the
    role this document belongs to, so there is nothing else to match.

    At that moment the caller holds no role yet, so the only principal it presents is
    its entity VRN. Trust is therefore written in terms of entities:
    vrn:iam::entity/admin/* trusts every admin, and a full entity VRN trusts one."""

    type: Literal[IdentityAccessPolicyType.TRUST] = IdentityAccessPolicyType.TRUST

    def covers(self, statement: IdentityAccessPolicyStatement,
        request: IdentityAccessRequest) -> bool:
        return (
            statement.matches_principal(request.principals)
            and statement.matches_action(request.action)
        )
