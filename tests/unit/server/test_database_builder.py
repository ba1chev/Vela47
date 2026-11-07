import pathlib

from app.server.config import Config
from db.database_sqlite import DatabaseSqlite
from db.database_postgres import DatabasePostgres
from app.server.database_builder import build_database
from app.server.config_environment import ConfigEnvironment


def make_prod_config():
    return Config(
        environment = ConfigEnvironment.PROD,
        database_host = "vela47.abc.eu-central-1.rds.amazonaws.com",
        database_name = "vela47",
        database_secret_id = "rds!db-123",
        aws_region = "eu-central-1",
        token_secret = "t" * 32
    )


class TestDatabaseBuilder:
    def test_dev_builds_sqlite_on_the_configured_file(self):
        database = build_database(Config(sqlite_path = pathlib.Path("/tmp/x.sqlite3")))
        assert isinstance(database, DatabaseSqlite)
        assert database.path == pathlib.Path("/tmp/x.sqlite3")

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
