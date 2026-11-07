from app.server.security import IdentityAccessRoleBase
from app.server.security import IdentityAccessRoleType
from app.server.security import IdentityAccessRoleUser
from app.server.security import IdentityAccessRoleAdmin
from app.server.security import IdentityAccessRoleGuest


IDENTITY_ACCESS_ROLE_REGISTRY: dict[IdentityAccessRoleType, type[IdentityAccessRoleBase]] = {
    IdentityAccessRoleType.ADMIN: IdentityAccessRoleAdmin,
    IdentityAccessRoleType.USER: IdentityAccessRoleUser,
    IdentityAccessRoleType.GUEST: IdentityAccessRoleGuest
}
