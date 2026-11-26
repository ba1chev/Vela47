from enum import Enum

from app.server.config_platform import ConfigPlatform


class ConfigEnvironment(str, Enum):
    """Enumerates where the server is running. LOCAL is a developer's machine; DEV,
    STAGING and PROD are deployed to AWS, built from the same release and told apart only
    by the names and sizes of their resources (see deploy/terraform). The platform an
    environment runs on decides where everything the server needs comes from, and an
    AWS environment has no default for anything whose absence would quietly weaken it."""

    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"

    @property
    def platform(self) -> ConfigPlatform:
        return ConfigPlatform.LOCAL if self is ConfigEnvironment.LOCAL else ConfigPlatform.AWS
