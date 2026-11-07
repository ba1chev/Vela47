from typing import Any, Callable
from sqlalchemy.engine import URL, Engine
from sqlalchemy import create_engine, event

from db import DatabaseBase
from db import DatabaseType
from db import DatabaseCredentials


class DatabasePostgres(DatabaseBase):
    """The production database: PostgreSQL on an RDS Multi-AZ instance, reached through
    psycopg 3.

    Credentials are not part of the URL. They come from a provider called every time the
    pool opens a new connection, because on RDS the password lives in Secrets Manager and
    rotates there: a password read once at startup would work until the first rotation
    and then lock the server out of its own database. Keeping them out of the URL also
    keeps the password out of every place SQLAlchemy prints one.

    The pool is set up for failover. When Multi-AZ fails over, the endpoint's DNS moves
    to the standby and every open connection dies; pre-ping tests a connection before
    handing it out and replaces a dead one rather than failing the request with it, and
    recycling retires connections before the network gets a chance to cut them. The
    connect timeout makes an unreachable primary fail fast instead of hanging a thread.

    sslmode defaults to 'require' — encrypted, which RDS supports out of the box.
    'verify-full' authenticates the server as well, and needs the RDS CA bundle on the
    host."""

    DRIVER = "postgresql+psycopg"
    POOL_RECYCLE_SECONDS = 1800
    CONNECT_TIMEOUT_SECONDS = 10

    def __init__(self, host: str, credentials: Callable[[], DatabaseCredentials],
        name: str = "vela47", port: int = 5432, ssl_mode: str = "require",
        pool_size: int = 5, max_overflow: int = 5) -> None:
        super().__init__()
        self._host: str = host
        self._credentials: Callable[[], DatabaseCredentials] = credentials
        self._name: str = name
        self._port: int = port
        self._ssl_mode: str = ssl_mode
        self._pool_size: int = pool_size
        self._max_overflow: int = max_overflow

    @property
    def database_type(self) -> DatabaseType:
        return DatabaseType.POSTGRES

    @property
    def url(self) -> URL:
        return URL.create(
            self.DRIVER,
            host = self._host,
            port = self._port,
            database = self._name,
            query = {"sslmode": self._ssl_mode}
        )

    def _inject_credentials(self, dialect: Any, connection_record: Any,
        connection_arguments: Any, connection_parameters: dict[str, Any]) -> None:
        credentials = self._credentials()
        connection_parameters["user"] = credentials.username
        connection_parameters["password"] = credentials.password.get_secret_value()

    def _create_engine(self) -> Engine:
        engine = create_engine(
            self.url,
            pool_pre_ping = True,
            pool_recycle = self.POOL_RECYCLE_SECONDS,
            pool_size = self._pool_size,
            max_overflow = self._max_overflow,
            connect_args = {"connect_timeout": self.CONNECT_TIMEOUT_SECONDS}
        )
        event.listen(engine, "do_connect", self._inject_credentials)
        return engine
