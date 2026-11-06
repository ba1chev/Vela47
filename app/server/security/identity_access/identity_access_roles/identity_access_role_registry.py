from app.server.security.identity_access.identity_access_roles.identity_access_role_base import IdentityAccessRoleBase
from app.server.security.identity_access.identity_access_roles.identity_access_role_type import IdentityAccessRoleType
from app.server.security.identity_access.identity_access_roles.identity_access_role_user import IdentityAccessRoleUser
from app.server.security.identity_access.identity_access_roles.identity_access_role_admin import IdentityAccessRoleAdmin
from app.server.security.identity_access.identity_access_roles.identity_access_role_guest import IdentityAccessRoleGuest


IDENTITY_ACCESS_ROLE_REGISTRY: dict[IdentityAccessRoleType, type[IdentityAccessRoleBase]] = {
    IdentityAccessRoleType.ADMIN: IdentityAccessRoleAdmin,
    IdentityAccessRoleType.USER: IdentityAccessRoleUser,
    IdentityAccessRoleType.GUEST: IdentityAccessRoleGuest
}
