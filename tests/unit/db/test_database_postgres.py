from db import DatabaseType
from db import DatabasePostgres
from db import DatabaseCredentials
from tests.fixtures.db.recording_connection import RecordingConnection


def make_database(calls = None):
    def credentials():
        if calls is not None:
            calls.append(1)
        return DatabaseCredentials(username = "vela", password = "p@ss/w:rd")

    return DatabasePostgres(host = "x.rds.amazonaws.com", credentials = credentials)


class TestDatabasePostgres:
    def test_its_type_is_postgres(self):
        assert make_database().database_type is DatabaseType.POSTGRES

    def test_the_url_names_the_endpoint_database_and_ssl_mode(self):
        url = make_database().url
        assert url.host == "x.rds.amazonaws.com"
        assert url.port == 5432
        assert url.database == "vela47"
        assert url.query["sslmode"] == "require"

    def test_the_url_never_carries_credentials(self):
        url = make_database().url
        assert url.username is None and url.password is None
        assert "p@ss" not in url.render_as_string(hide_password = False)

    def test_credentials_are_not_fetched_until_a_connection_is_opened(self):
        calls = []
        make_database(calls)
        assert calls == []

    def test_every_new_connection_fetches_credentials_afresh(self):
        calls = []
        database = make_database(calls)
        for _ in range(3):
            database._inject_credentials(None, None, None, {})
        assert len(calls) == 3

    def test_injected_credentials_reach_the_connection_untouched(self):
        parameters = {}
        make_database()._inject_credentials(None, None, None, parameters)
        assert parameters == {"user": "vela", "password": "p@ss/w:rd"}

    def test_the_schema_is_created_under_an_advisory_lock_held_until_the_transaction_ends(self):
        connection = RecordingConnection()
        make_database()._lock_schema(connection)
        assert connection.statements == [
            ("SELECT pg_advisory_xact_lock(:key)", {"key": DatabasePostgres.SCHEMA_LOCK_KEY})
        ]
