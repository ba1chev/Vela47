from app.server.security import IdentityAccessRoleBase
from app.server.security import IdentityAccessRoleType
from app.server.security import IdentityAccessTrustPolicy
from app.server.security import IdentityAccessPolicyEffect
from app.server.security import IdentityAccessPolicyStatement
from app.server.security import IdentityAccessPermissionPolicy


class IdentityAccessRoleUser(IdentityAccessRoleBase):
    """Everyday use of the server: running the agent, and nothing to do with identity.
    Trusted by users and by admins, so an admin can work without carrying admin rights
    around — the role is what gets checked, not who is holding it.

    What it may touch is meant to grow through ${principal.id}: a statement such as
    vrn:session:${principal.id}:* grants every user their own resources and nobody
    else's, with one statement for all of them."""

    @property
    def role_type(self) -> IdentityAccessRoleType:
        return IdentityAccessRoleType.USER

    @property
    def trust_policy(self) -> IdentityAccessTrustPolicy:
        return IdentityAccessTrustPolicy(
            name = "UserTrust",
            statements = [
                IdentityAccessPolicyStatement(
                    sid = "UsersAndAdminsAtWork",
                    effect = IdentityAccessPolicyEffect.ALLOW,
                    principals = ["vrn:iam::entity/user/*", "vrn:iam::entity/admin/*"],
                    actions = ["iam:AssumeRole"]
                )
            ]
        )

    @property
    def permission_policies(self) -> list[IdentityAccessPermissionPolicy]:
        return [
            IdentityAccessPermissionPolicy(
                name = "UserAccess",
                statements = [
                    IdentityAccessPolicyStatement(
                        sid = "RunAgents",
                        effect = IdentityAccessPolicyEffect.ALLOW,
                        actions = ["agent:Run"],
                        resources = ["vrn:agent::*"]
                    )
                ]
            )
        ]

    @property
    def max_session_seconds(self) -> int:
        return 43200
