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
    factory = DatabaseFactory()

    if config.environment is ConfigEnvironment.DEV:
        return factory.create(DatabaseType.SQLITE, path = config.database.sqlite_path)

    def credentials() -> DatabaseCredentials:
        secret = secret_reader(config.database.secret_id, config.aws_region)
        return DatabaseCredentials(username = secret["username"], password = secret["password"])

    return factory.create(
        DatabaseType.POSTGRES,
        host = config.database.host,
        port = config.database.port,
        name = config.database.name,
        ssl_mode = config.database.ssl_mode,
        credentials = credentials
    )
