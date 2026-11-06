from app.server.security.identity_access.identity_entities.identity_entity_base import IdentityEntityBase
from app.server.security.identity_access.identity_entities.identity_entity_type import IdentityEntityType
from app.server.security.identity_access.identity_entities.identity_entity_user import IdentityEntityUser
from app.server.security.identity_access.identity_entities.identity_entity_admin import IdentityEntityAdmin
from app.server.security.identity_access.identity_entities.identity_entity_guest import IdentityEntityGuest


IDENTITY_ENTITY_REGISTRY: dict[IdentityEntityType, type[IdentityEntityBase]] = {
    IdentityEntityType.ADMIN: IdentityEntityAdmin,
    IdentityEntityType.USER: IdentityEntityUser,
    IdentityEntityType.GUEST: IdentityEntityGuest
}
