from app.server.security.identity_access.identity_access_roles.identity_access_role_base import IdentityAccessRoleBase
from app.server.security.identity_access.identity_access_roles.identity_access_role_type import IdentityAccessRoleType
from app.server.security.identity_access.identity_access_policies.identity_access_policy_effect import IdentityAccessPolicyEffect
from app.server.security.identity_access.identity_access_policies.identity_access_policy_statement import IdentityAccessPolicyStatement
from app.server.security.identity_access.identity_access_policies.identity_access_trust_policy.identity_access_trust_policy import IdentityAccessTrustPolicy
from app.server.security.identity_access.identity_access_policies.identity_access_permission_policy.identity_access_permission_policy import IdentityAccessPermissionPolicy


class IdentityAccessRoleGuest(IdentityAccessRoleBase):
    """What an anonymous visitor may do: run the agent, and never anything to do with
    identity. Trusted by guest entities only.

    The explicit deny on iam:* is defence in depth rather than a necessity — nothing
    here allows it anyway. It is there because a deny cannot be overridden, so no
    resource policy attached later, and no careless widening of the allow above it, can
    ever let an anonymous caller manage accounts.

    Sessions last twelve hours. A leaked guest token grants only what anyone can obtain
    by asking for one, so there is nothing a short lifetime would protect."""

    @property
    def role_type(self) -> IdentityAccessRoleType:
        return IdentityAccessRoleType.GUEST

    @property
    def trust_policy(self) -> IdentityAccessTrustPolicy:
        return IdentityAccessTrustPolicy(
            name = "GuestTrust",
            statements = [
                IdentityAccessPolicyStatement(
                    sid = "GuestEntitiesOnly",
                    effect = IdentityAccessPolicyEffect.ALLOW,
                    principals = ["vrn:iam::entity/guest/*"],
                    actions = ["iam:AssumeRole"]
                )
            ]
        )

    @property
    def permission_policies(self) -> list[IdentityAccessPermissionPolicy]:
        return [
            IdentityAccessPermissionPolicy(
                name = "GuestAccess",
                statements = [
                    IdentityAccessPolicyStatement(
                        sid = "RunAgents",
                        effect = IdentityAccessPolicyEffect.ALLOW,
                        actions = ["agent:Run"],
                        resources = ["vrn:agent::*"]
                    ),
                    IdentityAccessPolicyStatement(
                        sid = "NeverIdentity",
                        effect = IdentityAccessPolicyEffect.DENY,
                        actions = ["iam:*"],
                        resources = ["*"]
                    )
                ]
            )
        ]

    @property
    def max_session_seconds(self) -> int:
        return 43200
