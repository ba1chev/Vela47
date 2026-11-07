from db import DatabaseBase
from db import DatabaseType
from db import DatabaseSqlite
from db import DatabasePostgres


DATABASE_REGISTRY: dict[DatabaseType, type[DatabaseBase]] = {
    DatabaseType.SQLITE: DatabaseSqlite,
    DatabaseType.POSTGRES: DatabasePostgres
}
