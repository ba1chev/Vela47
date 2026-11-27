from enum import Enum


class ConfigPlatform(str, Enum):
    """Enumerates what an environment runs on, which decides the code path of the server:
    the model client, the sandbox, the web search and the embedding model. LOCAL is a
    developer's machine: Ollama on the host unless Bedrock is chosen, the sandbox as
    Docker containers, SQLite or a local PostgreSQL, settings from the environment. AWS is every deployed environment:
    Bedrock, the sandbox Lambda function, RDS and Secrets Manager. Environments on the
    same platform run the same code and differ only in names and sizes."""

    LOCAL = "local"
    AWS = "aws"
