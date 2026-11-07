from app.server.security import IdentityEntityBase
from app.server.security import IdentityEntityType
from app.server.security import IdentityEntityUser
from app.server.security import IdentityEntityAdmin
from app.server.security import IdentityEntityGuest


IDENTITY_ENTITY_REGISTRY: dict[IdentityEntityType, type[IdentityEntityBase]] = {
    IdentityEntityType.ADMIN: IdentityEntityAdmin,
    IdentityEntityType.USER: IdentityEntityUser,
    IdentityEntityType.GUEST: IdentityEntityGuest
}
