from abc import ABC, abstractmethod

from app.server.security.identity_access.identity_access_vrn import format_role_vrn
from app.server.security.identity_access.identity_access_roles.identity_access_role_type import IdentityAccessRoleType
from app.server.security.identity_access.identity_access_policies.identity_access_trust_policy.identity_access_trust_policy import IdentityAccessTrustPolicy
from app.server.security.identity_access.identity_access_policies.identity_access_permission_policy.identity_access_permission_policy import IdentityAccessPermissionPolicy


class IdentityAccessRoleBase(ABC):
    """Abstract base for a role: a set of permissions a principal may act through for a
    limited time, together with the trust policy deciding which principals may. Roles
    hold no credentials and nobody is a role — an entity assumes one and receives a role
    session, exactly as with AWS IAM roles and STS.

    Splitting who you are from what you may do is what makes the trust policy both
    necessary and useful. Permissions are written once per role instead of once per
    person, and widening who may hold them is an edit to one trust policy.

    The roles are code while the policies they return are data. The built-in roles are a
    closed set the server cannot run without, so each lives in a file of its own that
    answers, in one read, who can become it and what it can do. A role defined at
    runtime would be one more subclass that takes its documents in its constructor —
    nothing that evaluates roles reads anything but the properties below."""

    @property
    @abstractmethod
    def role_type(self) -> IdentityAccessRoleType:
        raise NotImplementedError("Must be implemented")

    @property
    @abstractmethod
    def trust_policy(self) -> IdentityAccessTrustPolicy:
        raise NotImplementedError("Must be implemented")

    @property
    @abstractmethod
    def permission_policies(self) -> list[IdentityAccessPermissionPolicy]:
        raise NotImplementedError("Must be implemented")

    @property
    @abstractmethod
    def max_session_seconds(self) -> int:
        raise NotImplementedError("Must be implemented")

    @property
    def vrn(self) -> str:
        return format_role_vrn(self.role_type)
