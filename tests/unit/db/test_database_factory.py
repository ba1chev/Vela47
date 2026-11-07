import pytest

from db import DatabaseType
from db import DatabaseSqlite
from db import DatabaseFactory
from db import DatabasePostgres
from db import DATABASE_REGISTRY
from db import DatabaseCredentials


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
