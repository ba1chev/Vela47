from typing import Optional
from abc import ABC, abstractmethod

from app.server.security import IdentityEntityBase
from app.server.security import IdentityAccessResourcePolicy


class IdentityAccessStoreBase(ABC):
    """Abstract base for wherever identities and resource policies are kept. The service
    above it owns every rule — who may be created, how names are normalised, what a
    session may do — and the store only remembers. Swapping the in-memory store for the
    database therefore changes nothing above this interface, which is the whole reason
    the store is separate from the service.

    add_entity() must refuse a name that is already taken, and must do so atomically.
    Unique names are what make sign-in by name unambiguous, and a check made by the
    caller before inserting would race a concurrent creation of the same name."""

    @abstractmethod
    def add_entity(self, entity: IdentityEntityBase) -> None:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def get_entity(self, entity_id: str) -> Optional[IdentityEntityBase]:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def find_entity(self, name: str) -> Optional[IdentityEntityBase]:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def put_resource_policy(self, resource: str, policy: IdentityAccessResourcePolicy) -> None:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def get_resource_policy(self, resource: str) -> Optional[IdentityAccessResourcePolicy]:
        raise NotImplementedError("Must be implemented")
