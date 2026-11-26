import pathlib
from alembic import command
from sqlalchemy import inspect
from alembic.config import Config
from sqlalchemy.engine import Connection
from alembic.script import ScriptDirectory
from alembic.migration import MigrationContext

from db import TABLE_REGISTRY

MIGRATIONS_DIRECTORY = pathlib.Path(__file__).resolve().parent / "migrations"
BASELINE_REVISION = "0001"


class DatabaseMigrator:
    """Brings a database to the newest revision in db/migrations, over a connection the
    caller already holds inside a transaction, so on PostgreSQL a failed migration rolls
    back as a whole and the schema lock of DatabaseBase covers it.

    A database created by create_all before migrations existed has every table of the
    baseline and no alembic_version table; it is stamped at the baseline instead of
    having its tables created twice. Revisions must keep working with the release before
    them, because during a deployment both releases run against the same schema."""

    def __init__(self, connection: Connection) -> None:
        self._connection: Connection = connection
        self._config: Config = Config()
        self._config.set_main_option("script_location", str(MIGRATIONS_DIRECTORY))
        self._config.attributes["connection"] = connection

    @property
    def head(self) -> str:
        return ScriptDirectory.from_config(self._config).get_current_head()

    @property
    def current(self) -> str | None:
        return MigrationContext.configure(self._connection).get_current_revision()

    def _predates_migrations(self) -> bool:
        tables = set(inspect(self._connection).get_table_names())
        return "alembic_version" not in tables and set(TABLE_REGISTRY) <= tables

    def upgrade(self) -> None:
        if self._predates_migrations():
            command.stamp(self._config, BASELINE_REVISION)
        command.upgrade(self._config, "head")
