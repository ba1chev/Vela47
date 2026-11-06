from typing import Any

from app.server.security.identity_access.identity_entities.identity_entity_base import IdentityEntityBase
from app.server.security.identity_access.identity_entities.identity_entity_type import IdentityEntityType
from app.server.security.identity_access.identity_entities.identity_entity_user import IdentityEntityUser
from app.server.security.identity_access.identity_entities.identity_entity_admin import IdentityEntityAdmin
from app.server.security.identity_access.identity_entities.identity_entity_guest import IdentityEntityGuest
from app.server.security.identity_access.identity_entities.identity_entity_factory.identity_entity_factory_base import IdentityEntityFactoryBase


class IdentityEntityFactory(IdentityEntityFactoryBase):
    """Concrete factory that maps each IdentityEntityType to its IdentityEntityBase
    subclass and delegates construction to it. Additional keyword arguments are
    forwarded verbatim, so callers supply name and password_hash for the kinds that
    need them, or id to rebuild a guest from its session, without the factory knowing
    which fields each kind takes.

    Registry reference:
      ADMIN -> IdentityEntityAdmin(name=<str>, password_hash=<str>)
      USER  -> IdentityEntityUser(name=<str>, password_hash=<str>)
      GUEST -> IdentityEntityGuest(id=<str>, optional)"""

    _registry: dict[IdentityEntityType, type[IdentityEntityBase]] = {
        IdentityEntityType.ADMIN: IdentityEntityAdmin,
        IdentityEntityType.USER: IdentityEntityUser,
        IdentityEntityType.GUEST: IdentityEntityGuest
    }

    def create(self, type: IdentityEntityType, **kwargs: Any) -> IdentityEntityBase:
        cls = self._registry.get(type)

        if cls is None:
            raise ValueError(
                f"No entity class registered for type '{type}'. "
                f"Known types: {list(self._registry)}"
            )

        return cls(**kwargs)
