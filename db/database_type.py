from enum import Enum


class DatabaseType(str, Enum):
    """Enumerates the database backends the server can run on. There are two because
    there are two places it runs: SQLITE is a single file on a developer's machine,
    created on first start and needing no server at all; POSTGRES is the RDS Multi-AZ
    instance the deployed server talks to. Both are reached through SQLAlchemy, so
    everything above the database — tables, stores, queries — is the same code for
    either, and only how the engine is built differs."""

    SQLITE = "sqlite"
    POSTGRES = "postgres"
