from uuid import uuid4

from app.server.security import IdentityEntityBase
from app.server.security import IdentityAccessStoreInMemory


class RacingIdentityAccessStore(IdentityAccessStoreInMemory):
    """An in-memory store where another server always wins the race to a new name:
    just before an entity is added, a rival with the same name and another id is stored,
    so the add is refused as a taken name. Lets a test replay two servers bootstrapping
    the same admin at once without running two of them."""

    def add_entity(self, entity: IdentityEntityBase) -> None:
        if self.find_entity(entity.name) is None:
            super().add_entity(entity.model_copy(update = {"id": uuid4().hex}))
        super().add_entity(entity)
