from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Iterator, Optional
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session, sessionmaker

from db import TableBase
from db import DatabaseType
from db import TABLE_REGISTRY


class DatabaseBase(ABC):
    """Abstract base for the database the server keeps its state in: built at startup,
    started once, shut down on the way out. Subclasses differ only in how the SQLAlchemy
    engine is built.

    start() creates every registered table that is missing and leaves the rest, in one
    transaction behind _lock_schema(), so servers starting together create them once.
    That holds while the schema grows by whole tables; changing a column will need
    migrations. transaction() is the only way in and a unit of work: committed when the
    block ends, rolled back when it raises."""

    def __init__(self) -> None:
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker[Session]] = None

    @property
    @abstractmethod
    def database_type(self) -> DatabaseType:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def _create_engine(self) -> Engine:
        raise NotImplementedError("Must be implemented")

    @property
    def started(self) -> bool:
        return self._engine is not None

    def _lock_schema(self, connection: Connection) -> None:
        return None

    def start(self) -> None:
        engine = self._create_engine()
        with engine.begin() as connection:
            self._lock_schema(connection)
            TableBase.metadata.create_all(
                connection,
                tables = [current_table.__table__ for current_table in TABLE_REGISTRY.values()]
            )
        self._engine = engine
        self._session_factory = sessionmaker(engine, expire_on_commit = False)

    def shutdown(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
        self._engine = None
        self._session_factory = None

    @contextmanager
    def transaction(self) -> Iterator[Session]:
        if self._session_factory is None:
            raise RuntimeError("The database is not started — call start() before using it.")

        with self._session_factory.begin() as session:
            yield session
