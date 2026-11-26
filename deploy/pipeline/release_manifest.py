import re
import yaml
import pathlib
from typing import Optional, Self
from pydantic import BaseModel, Field, field_validator

from deploy.pipeline import DatabaseChange
from deploy.pipeline import InfrastructureChange

SEMANTIC_VERSION = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
RELEASE_MANIFEST_PATH = pathlib.Path(__file__).resolve().parents[1] / "release.yaml"


class ReleaseManifest(BaseModel):
    """The release a commit becomes once it is merged into main, as deploy/release.yaml
    declares it: its version and the kind of change it carries for the infrastructure and
    for the schema. The pull request that changes what runs bumps the version and says
    what kind of change it is; ReleaseRules holds it to that, and the deployment refuses
    a Terraform plan that does more than the release declared."""

    model_config = {"frozen": True}

    version: str = Field(
        description = "Semantic version of the release, MAJOR.MINOR.PATCH. The git tag is "
            "v<version> and the images are tagged <version>."
    )
    infrastructure: InfrastructureChange = Field(
        description = "What the release does to the infrastructure of an environment."
    )
    database: DatabaseChange = Field(
        description = "What the release does to the schema of the database."
    )
    summary: str = Field(
        min_length = 1,
        description = "One line on what the release changes, shown on the release and in the "
            "deployment records."
    )

    @field_validator("version")
    @classmethod
    def validate_version(cls, version: str) -> str:
        if not SEMANTIC_VERSION.match(version):
            raise ValueError(f"'{version}' is not a semantic version (MAJOR.MINOR.PATCH).")
        return version

    @staticmethod
    def parse_version(version: str) -> Optional[tuple[int, int, int]]:
        found = SEMANTIC_VERSION.match(version)
        if found is None:
            return None
        major, minor, patch = (int(current) for current in found.groups())
        return major, minor, patch

    @property
    def version_key(self) -> tuple[int, int, int]:
        return self.parse_version(self.version)

    @property
    def breaking(self) -> bool:
        return self.infrastructure is InfrastructureChange.BREAKING or self.database is DatabaseChange.CONTRACT

    @classmethod
    def from_yaml(cls, text: str) -> Self:
        return cls.model_validate(yaml.safe_load(text))

    @classmethod
    def load(cls, path: pathlib.Path = RELEASE_MANIFEST_PATH) -> Self:
        return cls.from_yaml(pathlib.Path(path).read_text())
