from threading import Lock
from typing import Optional

from app.server.security import IdentityEntityBase
from app.server.security import IdentityAccessStoreBase
from app.server.security import IdentityAccessResourcePolicy


class IdentityAccessStoreInMemory(IdentityAccessStoreBase):
    """Keeps everything in dictionaries for the lifetime of the process — the part
    SandboxPoolInMemory plays for sandboxes. It lets the whole security layer be built,
    run and tested before the database exists, at the cost that everything it holds is
    gone on restart, including every account an admin created.

    Guarded by a lock because FastAPI runs synchronous endpoints on a thread pool, so two
    requests can create entities at the same moment. The duplicate-name check and the
    insert happen under the same lock, which is what makes add_entity() atomic."""

    def __init__(self) -> None:
        self._entities: dict[str, IdentityEntityBase] = {}
        self._entity_ids_by_name: dict[str, str] = {}
        self._resource_policies: dict[str, IdentityAccessResourcePolicy] = {}
        self._lock: Lock = Lock()

    def add_entity(self, entity: IdentityEntityBase) -> None:
        with self._lock:
            if entity.name in self._entity_ids_by_name:
                raise ValueError(f"The name '{entity.name}' is already taken.")
            if entity.id in self._entities:
                raise ValueError(f"An entity with id '{entity.id}' already exists.")

            self._entities[entity.id] = entity
            self._entity_ids_by_name[entity.name] = entity.id

    def get_entity(self, entity_id: str) -> Optional[IdentityEntityBase]:
        with self._lock:
            return self._entities.get(entity_id)

    def find_entity(self, name: str) -> Optional[IdentityEntityBase]:
        with self._lock:
            entity_id = self._entity_ids_by_name.get(name)
            return self._entities.get(entity_id) if entity_id is not None else None

    def put_resource_policy(self, resource: str, policy: IdentityAccessResourcePolicy) -> None:
        with self._lock:
            self._resource_policies[resource] = policy

    def get_resource_policy(self, resource: str) -> Optional[IdentityAccessResourcePolicy]:
        with self._lock:
            return self._resource_policies.get(resource)

    def __len__(self) -> int:
        with self._lock:
            return len(self._entities)
