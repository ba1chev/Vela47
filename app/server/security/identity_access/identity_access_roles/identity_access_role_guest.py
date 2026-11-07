from app.server.security import IdentityAccessRoleBase
from app.server.security import IdentityAccessRoleType
from app.server.security import IdentityAccessTrustPolicy
from app.server.security import IdentityAccessPolicyEffect
from app.server.security import IdentityAccessPolicyStatement
from app.server.security import IdentityAccessPermissionPolicy


class IdentityAccessRoleGuest(IdentityAccessRoleBase):
    """What an anonymous visitor may do: run the agents and keep conversations and
    documents of its own, and never anything to do with identity. Trusted by guest
    entities only.

    A guest's conversations and documents are granted through ${principal.id} like a
    user's, but a guest is only the principal its token names. Once the token expires
    the next visit is a different guest, and what the earlier one left stays in the
    database without anyone who can reach it.

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
                        sid = "OwnSessions",
                        effect = IdentityAccessPolicyEffect.ALLOW,
                        actions = ["session:*"],
                        resources = ["vrn:session:${principal.id}:*"]
                    ),
                    IdentityAccessPolicyStatement(
                        sid = "OwnKnowledge",
                        effect = IdentityAccessPolicyEffect.ALLOW,
                        actions = ["knowledge:*"],
                        resources = ["vrn:knowledge:${principal.id}:*"]
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
