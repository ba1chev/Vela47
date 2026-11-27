from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone
from alembic.script import ScriptDirectory
from alembic.migration import MigrationContext
from alembic.autogenerate import compare_metadata
from sqlalchemy import create_engine, inspect, text

from db import TableBase
from db import DatabaseSqlite
from db import TABLE_REGISTRY
from db import DatabaseMigrator
from db import BASELINE_REVISION
from db import MIGRATIONS_DIRECTORY


def make_engine():
    return create_engine("sqlite://", poolclass = StaticPool, connect_args = {"check_same_thread": False})


def migrate(engine):
    with engine.begin() as connection:
        DatabaseMigrator(connection).upgrade()


class TestDatabaseMigrator:
    def test_a_new_database_is_migrated_to_the_head(self):
        engine = make_engine()
        migrate(engine)
        with engine.connect() as connection:
            migrator = DatabaseMigrator(connection)
            assert migrator.current == migrator.head

    def test_the_revisions_build_exactly_the_schema_the_tables_describe(self):
        engine = make_engine()
        migrate(engine)
        with engine.connect() as connection:
            context = MigrationContext.configure(connection, opts = {"compare_type": True})
            assert compare_metadata(context, TableBase.metadata) == []

    def test_migrating_twice_changes_nothing(self):
        engine = make_engine()
        migrate(engine)
        migrate(engine)
        with engine.connect() as connection:
            assert DatabaseMigrator(connection).current == DatabaseMigrator(connection).head

    def test_a_database_created_before_migrations_is_stamped_and_keeps_its_rows(self):
        engine = make_engine()
        with engine.begin() as connection:
            TableBase.metadata.create_all(connection, tables = [current.__table__ for current in TABLE_REGISTRY.values()])
            connection.execute(text(
                "INSERT INTO identity_entities VALUES ('a', 'user', 'ana', 'h', :created_at)"
            ), {"created_at": datetime.now(timezone.utc)})
        migrate(engine)
        with engine.connect() as connection:
            assert DatabaseMigrator(connection).current is not None
            assert connection.execute(text("SELECT count(*) FROM identity_entities")).scalar() == 1

    def test_the_document_trace_revision_adds_its_column_once(self):
        engine = make_engine()
        migrate(engine)
        with engine.connect() as connection:
            columns = [current["name"] for current in inspect(connection).get_columns("knowledge_documents")]
        assert columns.count("trace") == 1

    def test_the_history_is_one_line_from_the_baseline(self):
        script = ScriptDirectory(str(MIGRATIONS_DIRECTORY))
        revisions = list(script.walk_revisions())
        assert len(script.get_heads()) == 1
        assert revisions[-1].revision == BASELINE_REVISION and revisions[-1].down_revision is None

    def test_starting_a_database_migrates_it(self):
        database = DatabaseSqlite()
        database.start()
        with database._engine.connect() as connection:
            assert DatabaseMigrator(connection).current == DatabaseMigrator(connection).head
