import pathlib

from db import DatabaseConfig
from db import DatabaseSqlite
from db import DatabasePostgres
from db import DatabaseCredentials
from app.server.config import Config
from app.server.builders import build_database
from app.server.config_environment import ConfigEnvironment


def make_prod_config():
    return Config(
        environment = ConfigEnvironment.PROD,
        database = DatabaseConfig(
            host = "vela47.abc.eu-central-1.rds.amazonaws.com",
            name = "vela47",
            secret_id = "rds!db-123"
        ),
        aws_region = "eu-central-1",
        token_secret = "t" * 32
    )


class TestDatabaseBuilder:
    def test_dev_builds_sqlite_on_the_configured_file(self):
        database = build_database(Config(database = DatabaseConfig(sqlite_path = pathlib.Path("/tmp/x.sqlite3"))))
        assert isinstance(database, DatabaseSqlite)
        assert database.path == pathlib.Path("/tmp/x.sqlite3")

    def test_dev_with_a_database_host_builds_postgres_with_the_configured_credentials(self):
        reads = []
        config = Config(
            database = DatabaseConfig(host = "10.111.0.2", ssl_mode = "disable"),
            database_credentials = DatabaseCredentials(username = "vela47", password = "local-password")
        )
        database = build_database(config, lambda secret_id, region: reads.append(secret_id) or {})
        parameters = {}
        database._inject_credentials(None, None, None, parameters)
        assert isinstance(database, DatabasePostgres)
        assert database.url.host == "10.111.0.2" and database.url.query["sslmode"] == "disable"
        assert parameters == {"user": "vela47", "password": "local-password"}
        assert reads == []

    def test_prod_builds_postgres_on_the_configured_endpoint(self):
        database = build_database(make_prod_config(), lambda secret_id, region: {})
        assert isinstance(database, DatabasePostgres)
        assert database.url.host == "vela47.abc.eu-central-1.rds.amazonaws.com"

    def test_building_does_not_read_the_database_secret(self):
        reads = []
        build_database(make_prod_config(), lambda secret_id, region: reads.append(secret_id) or {})
        assert reads == []

    def test_each_new_connection_reads_the_rds_secret_from_its_region(self):
        reads = []

        def reader(secret_id, region):
            reads.append((secret_id, region))
            return {"username": "vela", "password": "rotated-password"}

        parameters = {}
        build_database(make_prod_config(), reader)._inject_credentials(None, None, None, parameters)
        assert reads == [("rds!db-123", "eu-central-1")]
        assert parameters == {"user": "vela", "password": "rotated-password"}
