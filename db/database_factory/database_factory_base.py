from typing import Any
from abc import ABC, abstractmethod

from db.database_base import DatabaseBase
from db.database_type import DatabaseType


class DatabaseFactoryBase(ABC):
    """Abstract factory that defines the contract for creating DatabaseBase instances.
    Lets the server name the database it wants by type — the form in which the choice is
    derived from configuration — without importing the concrete backends."""

    @abstractmethod
    def create(self, type: DatabaseType, **kwargs: Any) -> DatabaseBase:
        raise NotImplementedError("Must be implemented")
