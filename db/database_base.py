from abc import ABC, abstractmethod
from sqlalchemy.engine import Engine
from contextlib import contextmanager
from typing import Iterator, Optional
from sqlalchemy.orm import Session, sessionmaker

from db import TableBase
from db import DatabaseType
from db import TABLE_REGISTRY


class DatabaseBase(ABC):
    """Abstract base for the database the server keeps its state in — the counterpart of
    SandboxPoolBase: built at startup, started once, shut down on the way out. Concrete
    subclasses differ only in how the SQLAlchemy engine is built; everything above this
    class goes through transaction() and never learns which backend answered.

    start() creates every registered table that does not exist yet and leaves existing
    ones untouched. That is enough while the schema grows only by whole tables. The day a
    column has to change on a table that already holds data, schema migrations (Alembic)
    have to take over from it.

    transaction() is the only way in, and it is a unit of work: everything done inside
    the block is committed together when the block ends normally and rolled back together
    when it raises. A store therefore cannot leave half a change behind, and raising is
    all it takes to abandon one."""

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

    def start(self) -> None:
        engine = self._create_engine()
        TableBase.metadata.create_all(
            engine,
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
