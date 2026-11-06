from app.server.security.identity_access.identity_access_roles.identity_access_role_base import IdentityAccessRoleBase
from app.server.security.identity_access.identity_access_roles.identity_access_role_type import IdentityAccessRoleType
from app.server.security.identity_access.identity_access_policies.identity_access_policy_effect import IdentityAccessPolicyEffect
from app.server.security.identity_access.identity_access_policies.identity_access_policy_statement import IdentityAccessPolicyStatement
from app.server.security.identity_access.identity_access_policies.identity_access_trust_policy.identity_access_trust_policy import IdentityAccessTrustPolicy
from app.server.security.identity_access.identity_access_policies.identity_access_permission_policy.identity_access_permission_policy import IdentityAccessPermissionPolicy


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
