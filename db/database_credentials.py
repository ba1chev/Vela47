from pydantic import BaseModel, Field, SecretStr


class DatabaseCredentials(BaseModel):
    """The user name and password a database connection authenticates with. A model of
    its own rather than two strings because credentials are fetched, not configured: on
    RDS the password lives in Secrets Manager and rotates there, so the database asks
    for credentials each time it opens a connection instead of being handed them once."""

    model_config = {"frozen": True}

    username: str = Field(
        min_length = 1,
        description = "Database user to connect as — the RDS master user, or a user created "
            "for the server."
    )
    password: SecretStr = Field(
        description = "Password of that user. A SecretStr, so it never appears in a repr, a "
            "log line or an error message."
    )
