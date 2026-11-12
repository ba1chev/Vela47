from typing import Any, Callable
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import URL, Connection, Engine

from db import DatabaseBase
from db import DatabaseType
from db import DatabaseCredentials


class DatabasePostgres(DatabaseBase):
    """The production database: PostgreSQL on an RDS Multi-AZ instance through psycopg
    3. Credentials are not in the URL; a provider is called for every new connection,
    because the password rotates in Secrets Manager and one read at startup would lock
    the server out after the first rotation.

    The pool is set up for failover: pre-ping replaces connections that died when the
    endpoint moved to the standby, recycling retires them before the network cuts them,
    and the connect timeout makes an unreachable primary fail fast. sslmode defaults to
    'require'. The schema is created under a transaction-level advisory lock, because two
    servers creating the same tables at once make one of them fail."""

    DRIVER = "postgresql+psycopg"
    POOL_RECYCLE_SECONDS = 1800
    CONNECT_TIMEOUT_SECONDS = 10
    SCHEMA_LOCK_KEY = 4747

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

    def _lock_schema(self, connection: Connection) -> None:
        connection.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": self.SCHEMA_LOCK_KEY})

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
