import pathlib
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine import URL, Engine

from db import DatabaseBase
from db import DatabaseType


class DatabaseSqlite(DatabaseBase):
    """The development database: a single SQLite file, created on first start, with no
    server to install or run. Deleting the file starts the next run from an empty schema.

    Given no path it lives in memory instead, which is what the tests use. An in-memory
    SQLite database belongs to the one connection that created it, so that mode pins the
    engine to a single shared connection — otherwise every thread would open a database
    of its own and see none of the others' writes.

    The file mode lets connections cross threads, since FastAPI serves synchronous
    endpoints from a thread pool, and waits for a write lock for up to the busy timeout
    instead of failing the moment two requests write at once."""

    BUSY_TIMEOUT_SECONDS = 30

    def __init__(self, path: Optional[pathlib.Path] = None) -> None:
        super().__init__()
        self._path: Optional[pathlib.Path] = pathlib.Path(path) if path is not None else None

    @property
    def database_type(self) -> DatabaseType:
        return DatabaseType.SQLITE

    @property
    def path(self) -> Optional[pathlib.Path]:
        return self._path

    def _create_engine(self) -> Engine:
        if self._path is None:
            return create_engine(
                "sqlite://",
                poolclass = StaticPool,
                connect_args = {"check_same_thread": False}
            )

        self._path.parent.mkdir(parents = True, exist_ok = True)
        return create_engine(
            URL.create("sqlite", database = str(self._path)),
            connect_args = {"check_same_thread": False, "timeout": self.BUSY_TIMEOUT_SECONDS}
        )
