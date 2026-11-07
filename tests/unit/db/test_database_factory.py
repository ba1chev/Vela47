import pytest

from db.database_type import DatabaseType
from db.database_sqlite import DatabaseSqlite
from db.database_postgres import DatabasePostgres
from db.database_credentials import DatabaseCredentials
from db.database_factory.database_factory import DatabaseFactory
from db.database_factory.database_registry import DATABASE_REGISTRY


class TestDatabaseFactory:
    def test_every_database_type_is_registered(self):
        assert set(DATABASE_REGISTRY) == set(DatabaseType)

    def test_it_builds_sqlite(self):
        assert isinstance(DatabaseFactory().create(DatabaseType.SQLITE), DatabaseSqlite)

    def test_it_builds_postgres_with_forwarded_arguments(self):
        database = DatabaseFactory().create(
            DatabaseType.POSTGRES,
            host = "h",
            name = "other",
            credentials = lambda: DatabaseCredentials(username = "u", password = "p")
        )
        assert isinstance(database, DatabasePostgres)
        assert database.url.database == "other"

    def test_an_unknown_type_raises_value_error(self):
        with pytest.raises(ValueError):
            DatabaseFactory().create("oracle")
