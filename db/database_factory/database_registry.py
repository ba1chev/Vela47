from db.database_base import DatabaseBase
from db.database_type import DatabaseType
from db.database_sqlite import DatabaseSqlite
from db.database_postgres import DatabasePostgres


DATABASE_REGISTRY: dict[DatabaseType, type[DatabaseBase]] = {
    DatabaseType.SQLITE: DatabaseSqlite,
    DatabaseType.POSTGRES: DatabasePostgres
}
