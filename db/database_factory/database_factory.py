from typing import Any

from db import DatabaseBase
from db import DatabaseType
from db import DATABASE_REGISTRY
from db import DatabaseFactoryBase


class DatabaseFactory(DatabaseFactoryBase):
    """Concrete factory that maps each DatabaseType to its DatabaseBase subclass and
    delegates construction to it. Additional keyword arguments are forwarded verbatim,
    so the caller supplies a path for SQLite or an endpoint and a credentials provider
    for PostgreSQL without the factory knowing which backend takes which.

    Registry reference:
      SQLITE   -> DatabaseSqlite(path=<Path>, optional — None means in memory)
      POSTGRES -> DatabasePostgres(host=<str>, credentials=<Callable[[], DatabaseCredentials]>,
                  name=<str>, port=<int>, ssl_mode=<str>, pool_size=<int>, max_overflow=<int>)"""

    def create(self, type: DatabaseType, **kwargs: Any) -> DatabaseBase:
        cls = DATABASE_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No database class registered for type '{type}'. "
                f"Known types: {list(DATABASE_REGISTRY)}"
            )

        return cls(**kwargs)
