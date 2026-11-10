import pathlib
from typing import Optional
from pydantic import BaseModel, Field

DEFAULT_SQLITE_PATH = pathlib.Path(__file__).resolve().parent / "vela47.sqlite3"


class DatabaseConfig(BaseModel):
    """Where the database is and how to reach it: the SQLite file for development and the
    PostgreSQL endpoint on RDS for production. Plain data, like ModelConfig; which of the
    two is used is decided by whoever builds the database, not here.

    No password is part of it. On RDS the password lives in a secret that rotates, so only
    the secret's id is configured, and the database asks for credentials on every new
    connection."""

    model_config = {"frozen": True}

    sqlite_path: pathlib.Path = Field(
        default = DEFAULT_SQLITE_PATH,
        description = "SQLite only. The database file, by default db/vela47.sqlite3 in the "
            "repository. Created on first start."
    )
    host: Optional[str] = Field(
        default = None,
        description = "PostgreSQL only, required there. The RDS endpoint. On a Multi-AZ instance "
            "this name follows the primary through a failover."
    )
    port: int = Field(
        default = 5432,
        gt = 0,
        description = "PostgreSQL only. Port of the RDS instance."
    )
    name: str = Field(
        default = "vela47",
        min_length = 1,
        description = "PostgreSQL only. Database to use on the instance. Has to exist; set it as "
            "the initial database name when creating the RDS instance."
    )
    ssl_mode: str = Field(
        default = "require",
        description = "PostgreSQL only. libpq sslmode for the connection. 'require' encrypts; "
            "'verify-full' also checks the certificate against the RDS CA bundle."
    )
    secret_id: Optional[str] = Field(
        default = None,
        description = "PostgreSQL only, required there. ARN or name of the RDS-managed secret "
            "holding the username and password. Read for every new connection, never stored here."
    )
