import yaml
from typing import Self
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from deploy.pipeline import ReleaseManifest

IMAGE_NAMES = ("app", "sandbox")


class ReleaseArtifact(BaseModel):
    """What the delivery workflow stores as releases/<version>/release.yaml: the manifest
    of the release, the commit it was built from and the digest of every image it built.
    It never changes once written, and it is all an environment needs to run the release,
    since the app root of every environment reads its images from it."""

    model_config = {"frozen": True}

    manifest: ReleaseManifest = Field(description = "The release as deploy/release.yaml declared it.")
    commit: str = Field(min_length = 7, description = "Git commit the release was built from.")
    created_at: datetime = Field(description = "When the release was delivered, in UTC.")
    images: dict[str, str] = Field(
        description = "Image of every part of the release by name (app, sandbox), each an ECR URI "
            "pinned by digest."
    )

    @field_validator("images")
    @classmethod
    def validate_images(cls, images: dict[str, str]) -> dict[str, str]:
        if set(images) != set(IMAGE_NAMES):
            raise ValueError(f"A release has exactly the images {', '.join(IMAGE_NAMES)}.")
        unpinned = [current for current, uri in images.items() if "@sha256:" not in uri]
        if unpinned:
            raise ValueError(f"Every image of a release is pinned by digest, {', '.join(unpinned)} is not.")
        return images

    def to_yaml(self) -> str:
        document = {
            **self.manifest.model_dump(mode = "json"),
            "commit": self.commit,
            "created_at": self.created_at.isoformat(),
            "images": self.images
        }
        return yaml.safe_dump(document, sort_keys = False)

    @classmethod
    def from_yaml(cls, text: str) -> Self:
        document = yaml.safe_load(text)
        return cls(
            manifest = ReleaseManifest.model_validate({
                current: document[current] for current in ReleaseManifest.model_fields
            }),
            commit = document["commit"],
            created_at = document["created_at"],
            images = document["images"]
        )
