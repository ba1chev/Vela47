from app.server.security import IdentityAccessRoleBase
from app.server.security import IdentityAccessRoleType
from app.server.security import IdentityAccessTrustPolicy
from app.server.security import IdentityAccessPolicyEffect
from app.server.security import IdentityAccessPolicyStatement
from app.server.security import IdentityAccessPermissionPolicy


class IdentityAccessRoleGuest(IdentityAccessRoleBase):
    """What an anonymous visitor may do: run the agents and keep conversations and
    documents of its own, never anything to do with identity. Trusted by guest entities
    only, with twelve-hour sessions, since a leaked guest token grants only what anyone
    can get by asking for one.

    Own resources are granted through ${principal.id} as for a user, so once the token
    expires what the guest left stays in the database out of anyone's reach. The
    explicit deny on iam:* is defence in depth: a deny cannot be overridden, so no later
    resource policy or widened allow can let a guest manage accounts."""

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
