import pytest
import pathlib
import tempfile
from sqlalchemy import inspect
from datetime import datetime, timezone

from db import DatabaseType
from db import DatabaseSqlite
from db import TABLE_REGISTRY
from db import IdentityEntityTable


def make_row(id = "a" * 32, name = "ana"):
    return IdentityEntityTable(
        id = id, type = "user", name = name, password_hash = "h", created_at = datetime.now(timezone.utc)
    )


def make_started(path = None):
    database = DatabaseSqlite(path)
    database.start()
    return database


class TestDatabaseSqlite:
    def test_its_type_is_sqlite(self):
        assert DatabaseSqlite().database_type is DatabaseType.SQLITE

    def test_start_creates_every_registered_table(self):
        database = make_started()
        assert set(inspect(database._engine).get_table_names()) == set(TABLE_REGISTRY)

    def test_a_transaction_commits_when_the_block_ends(self):
        database = make_started()
        with database.transaction() as transaction:
            transaction.add(make_row())
        with database.transaction() as transaction:
            assert transaction.get(IdentityEntityTable, "a" * 32) is not None

    def test_a_transaction_rolls_back_everything_when_the_block_raises(self):
        database = make_started()
        with pytest.raises(RuntimeError):
            with database.transaction() as transaction:
                transaction.add(make_row())
                transaction.flush()
                raise RuntimeError("abandon")
        with database.transaction() as transaction:
            assert transaction.get(IdentityEntityTable, "a" * 32) is None

    def test_using_it_before_start_is_refused(self):
        with pytest.raises(RuntimeError):
            with DatabaseSqlite().transaction():
                pass

    def test_shutdown_makes_it_unusable_until_started_again(self):
        database = make_started()
        database.shutdown()
        assert not database.started
        with pytest.raises(RuntimeError):
            with database.transaction():
                pass

    def test_a_file_database_creates_its_directory_and_file(self):
        path = pathlib.Path(tempfile.mkdtemp()) / "nested" / "vela47.sqlite3"
        make_started(path).shutdown()
        assert path.is_file()

    def test_a_file_database_keeps_its_rows_across_a_restart(self):
        path = pathlib.Path(tempfile.mkdtemp()) / "vela47.sqlite3"
        first = make_started(path)
        with first.transaction() as transaction:
            transaction.add(make_row())
        first.shutdown()

        second = make_started(path)
        with second.transaction() as transaction:
            assert transaction.get(IdentityEntityTable, "a" * 32).name == "ana"

    def test_starting_again_leaves_existing_tables_and_rows_alone(self):
        path = pathlib.Path(tempfile.mkdtemp()) / "vela47.sqlite3"
        database = make_started(path)
        with database.transaction() as transaction:
            transaction.add(make_row())
        database.shutdown()
        database.start()
        with database.transaction() as transaction:
            assert transaction.get(IdentityEntityTable, "a" * 32) is not None
