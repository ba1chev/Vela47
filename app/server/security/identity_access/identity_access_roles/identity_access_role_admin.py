from app.server.security import IdentityAccessRoleBase
from app.server.security import IdentityAccessRoleType
from app.server.security import IdentityAccessTrustPolicy
from app.server.security import IdentityAccessPolicyEffect
from app.server.security import IdentityAccessPolicyStatement
from app.server.security import IdentityAccessPermissionPolicy


class IdentityAccessRoleAdmin(IdentityAccessRoleBase):
    """Full control over the server, identity included. Trusted by admin entities and
    nobody else — this trust policy is the single statement standing between a user and
    everything — and its sessions last an hour, because the most powerful token is the
    one that should go stale soonest if it leaks. An admin doing ordinary work is meant
    to sign in as the user role instead, which that role's trust policy allows."""

    @property
    def role_type(self) -> IdentityAccessRoleType:
        return IdentityAccessRoleType.ADMIN

    @property
    def trust_policy(self) -> IdentityAccessTrustPolicy:
        return IdentityAccessTrustPolicy(
            name = "AdminTrust",
            statements = [
                IdentityAccessPolicyStatement(
                    sid = "AdminEntitiesOnly",
                    effect = IdentityAccessPolicyEffect.ALLOW,
                    principals = ["vrn:iam::entity/admin/*"],
                    actions = ["iam:AssumeRole"]
                )
            ]
        )

    @property
    def permission_policies(self) -> list[IdentityAccessPermissionPolicy]:
        return [
            IdentityAccessPermissionPolicy(
                name = "AdministratorAccess",
                statements = [
                    IdentityAccessPolicyStatement(
                        sid = "Everything",
                        effect = IdentityAccessPolicyEffect.ALLOW,
                        actions = ["*"],
                        resources = ["*"]
                    )
                ]
            )
        ]

    @property
    def max_session_seconds(self) -> int:
        return 3600
