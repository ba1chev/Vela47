from typing import Callable

from db import DatabaseBase
from db import DatabaseType
from db import DatabaseFactory
from db import DatabaseCredentials
from app.server.config import Config
from app.server.config_secrets import read_secret
from app.server.config_environment import ConfigEnvironment


def build_database(config: Config,
    secret_reader: Callable[[str, str], dict[str, str]] = read_secret) -> DatabaseBase:
    """Turns the configuration into the database it describes: the SQLite file in DEV,
    the RDS instance in PROD. Built but not started — the lifespan starts it on a worker
    thread, since creating the schema talks to the database.

    In PROD the database is handed a credentials provider instead of credentials. It
    reads the RDS-managed secret, whose JSON carries username and password, each time a
    connection is opened — which is what keeps the server connected across the password
    rotations RDS performs on that secret."""
    factory = DatabaseFactory()

    if config.environment is ConfigEnvironment.DEV:
        return factory.create(DatabaseType.SQLITE, path = config.sqlite_path)

    def credentials() -> DatabaseCredentials:
        secret = secret_reader(config.database_secret_id, config.aws_region)
        return DatabaseCredentials(username = secret["username"], password = secret["password"])

    return factory.create(
        DatabaseType.POSTGRES,
        host = config.database_host,
        port = config.database_port,
        name = config.database_name,
        ssl_mode = config.database_ssl_mode,
        credentials = credentials
    )
