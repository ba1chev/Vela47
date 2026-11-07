from typing import Any

from app.server.security import IdentityEntityBase
from app.server.security import IdentityEntityType
from app.server.security import IDENTITY_ENTITY_REGISTRY
from app.server.security import IdentityEntityFactoryBase


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

    def create(self, type: IdentityEntityType, **kwargs: Any) -> IdentityEntityBase:
        cls = IDENTITY_ENTITY_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No entity class registered for type '{type}'. "
                f"Known types: {list(IDENTITY_ENTITY_REGISTRY)}"
            )

        return cls(**kwargs)
