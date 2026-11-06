from typing import Any
from abc import ABC, abstractmethod

from app.server.security.identity_access.identity_entities.identity_entity_base import IdentityEntityBase
from app.server.security.identity_access.identity_entities.identity_entity_type import IdentityEntityType


class IdentityEntityFactoryBase(ABC):
    """Abstract factory that defines the contract for creating IdentityEntityBase
    instances. Lets the identity service create an entity from its type alone — the form
    the type arrives in from a request body or, later, a database row — without knowing
    the concrete classes."""

    @abstractmethod
    def create(self, type: IdentityEntityType, **kwargs: Any) -> IdentityEntityBase:
        raise NotImplementedError("Must be implemented")
