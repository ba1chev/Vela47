from abc import ABC, abstractmethod

from app.server.security import format_role_vrn
from app.server.security import IdentityAccessRoleType
from app.server.security import IdentityAccessTrustPolicy
from app.server.security import IdentityAccessPermissionPolicy


class IdentityAccessRoleBase(ABC):
    """Abstract base for a role: permissions a principal may act through for a limited
    time, plus the trust policy deciding which principals may. Nobody is a role; an
    entity assumes one and receives a role session, as with AWS IAM roles and STS, so
    permissions are written once per role and widening who holds them is one trust
    policy edit.

    Roles are code and their policies data. The built-in roles are a closed set, each in
    a file of its own that says in one read who can become it and what it can do."""

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
