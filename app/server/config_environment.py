from enum import Enum


class ConfigEnvironment(str, Enum):
    """Enumerates where the server is running, which decides where everything it needs
    comes from. DEV is a developer's machine: a SQLite file next to the code, settings
    from the environment with a default for every one of them, and a throwaway signing
    key when none is given. PROD is EC2: PostgreSQL on RDS, every secret read from AWS
    Secrets Manager, and no default for anything whose absence would quietly weaken the
    server."""

    DEV = "dev"
    PROD = "prod"
