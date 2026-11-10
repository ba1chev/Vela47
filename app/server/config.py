import os
from typing import Any, Callable, Mapping, Optional, Self
from pydantic import BaseModel, Field, SecretStr, model_validator

from db import DatabaseConfig
from app.server.config_secrets import read_secret
from app.server.config_environment import ConfigEnvironment

DATABASE_VARIABLES = {
    "sqlite_path": "VELA47_SQLITE_PATH",
    "host": "VELA47_DATABASE_HOST",
    "port": "VELA47_DATABASE_PORT",
    "name": "VELA47_DATABASE_NAME",
    "ssl_mode": "VELA47_DATABASE_SSL_MODE",
    "secret_id": "VELA47_DATABASE_SECRET_ID"
}


class Config(BaseModel):
    """Everything the server needs to know about where it runs, and the only code that
    reads the environment or Secrets Manager. The rest of the server is handed a Config,
    so a test builds one in a line.

    Non-secret values come from VELA47_* environment variables. In PROD secrets never
    do: the token secret and the first admin are read once from an application secret,
    and the database password is not held here at all, since the database reads its
    RDS-managed secret for every new connection. DEV has a default for every field; PROD
    requires those it cannot run safely without, so a missing one fails the start."""

    model_config = {"frozen": True}

    environment: ConfigEnvironment = Field(
        default = ConfigEnvironment.DEV,
        description = "Where the server runs — VELA47_ENVIRONMENT, 'dev' or 'prod'. Decides the "
            "database backend and where secrets are read from."
    )
    database: DatabaseConfig = Field(
        default_factory = DatabaseConfig,
        description = "Where the database is and how to reach it. DEV: the SQLite file, "
            "VELA47_SQLITE_PATH. PROD: VELA47_DATABASE_HOST, _PORT, _NAME, _SSL_MODE and "
            "_SECRET_ID, of which the host and the secret are required."
    )
    aws_region: Optional[str] = Field(
        default = None,
        description = "PROD only, required. Region of the secrets — VELA47_AWS_REGION, falling back "
            "to AWS_REGION and AWS_DEFAULT_REGION."
    )
    knowledge_max_file_bytes: int = Field(
        default = 512 * 1024,
        gt = 0,
        description = "Most text one document may hold, in UTF-8 bytes, counted after it is "
            "extracted from the file — VELA47_KNOWLEDGE_MAX_FILE_BYTES. Every chunk of an upload "
            "is embedded before the request returns, so this also bounds how long an upload can "
            "take."
    )
    knowledge_max_upload_bytes: int = Field(
        default = 8 * 1024 * 1024,
        gt = 0,
        description = "Largest file one upload or URL import may be before its text is extracted, "
            "in bytes — VELA47_KNOWLEDGE_MAX_UPLOAD_BYTES. A PDF or Word document is far larger "
            "than the text inside it, so this bounds the work of reading one, while "
            "knowledge_max_file_bytes still bounds the text that is kept."
    )
    knowledge_max_owner_bytes: int = Field(
        default = 2 * 1024 * 1024,
        gt = 0,
        description = "Total size of the documents one owner may keep, in UTF-8 bytes — "
            "VELA47_KNOWLEDGE_MAX_OWNER_BYTES. All of an owner's chunks are loaded for every "
            "question the RAG agent answers, so this bounds the cost of a search as well as "
            "the size of the database."
    )
    token_secret: Optional[SecretStr] = Field(
        default = None,
        description = "Key that signs session tokens, at least 32 bytes. PROD: 'token_secret' in the "
            "application secret, required. DEV: VELA47_TOKEN_SECRET, optional — without it a key "
            "is generated per run and every restart signs everyone out."
    )
    admin_username: Optional[str] = Field(
        default = None,
        description = "Name of the admin to create on start if no entity has it yet. PROD: "
            "'admin_username' in the application secret. DEV: VELA47_ADMIN_USERNAME."
    )
    admin_password: Optional[SecretStr] = Field(
        default = None,
        description = "Password of that admin, at least 12 characters. PROD: 'admin_password' in the "
            "application secret. DEV: VELA47_ADMIN_PASSWORD. Unused once the admin exists."
    )

    @model_validator(mode = "after")
    def validate_production(self) -> Self:
        if self.environment is not ConfigEnvironment.PROD:
            return self

        missing = [
            current_name
            for current_name, current_value in (
                ("database.host", self.database.host),
                ("database.secret_id", self.database.secret_id),
                ("aws_region", self.aws_region),
                ("token_secret", self.token_secret)
            )
            if current_value is None
        ]
        if missing:
            raise ValueError(f"PROD cannot start without {', '.join(missing)}.")
        return self

    @classmethod
    def from_environment(cls, environ: Mapping[str, str] = os.environ,
        secret_reader: Callable[[str, str], dict[str, str]] = read_secret) -> "Config":
        environment = ConfigEnvironment(environ.get("VELA47_ENVIRONMENT", ConfigEnvironment.DEV.value))
        region = (
            environ.get("VELA47_AWS_REGION")
            or environ.get("AWS_REGION")
            or environ.get("AWS_DEFAULT_REGION")
        )
        values: dict[str, Any] = {
            "environment": environment,
            "database": DatabaseConfig(**{
                current_field: environ[current_variable]
                for current_field, current_variable in DATABASE_VARIABLES.items()
                if environ.get(current_variable)
            }),
            "aws_region": region,
            "knowledge_max_file_bytes": int(environ.get("VELA47_KNOWLEDGE_MAX_FILE_BYTES", 512 * 1024)),
            "knowledge_max_upload_bytes": int(environ.get("VELA47_KNOWLEDGE_MAX_UPLOAD_BYTES", 8 * 1024 * 1024)),
            "knowledge_max_owner_bytes": int(environ.get("VELA47_KNOWLEDGE_MAX_OWNER_BYTES", 2 * 1024 * 1024))
        }

        if environment is ConfigEnvironment.DEV:
            values.update(
                token_secret = environ.get("VELA47_TOKEN_SECRET") or None,
                admin_username = environ.get("VELA47_ADMIN_USERNAME") or None,
                admin_password = environ.get("VELA47_ADMIN_PASSWORD") or None
            )
            return cls(**values)

        app_secret_id = environ.get("VELA47_APP_SECRET_ID")
        if not app_secret_id or not region:
            raise ValueError(
                "PROD reads its secrets from AWS Secrets Manager and needs VELA47_APP_SECRET_ID "
                "and a region (VELA47_AWS_REGION) to find them."
            )

        app_secret = secret_reader(app_secret_id, region)
        values.update(
            token_secret = app_secret.get("token_secret"),
            admin_username = app_secret.get("admin_username"),
            admin_password = app_secret.get("admin_password")
        )
        return cls(**values)
