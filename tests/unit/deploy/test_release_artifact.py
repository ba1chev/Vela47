import pytest
from pydantic import ValidationError
from datetime import datetime, timezone

from deploy.pipeline import ReleaseArtifact
from deploy.pipeline import ReleaseManifest

APP = "1.dkr.ecr.eu-central-1.amazonaws.com/vela47-app@sha256:" + "a" * 64
SANDBOX = "1.dkr.ecr.eu-central-1.amazonaws.com/vela47-sandbox@sha256:" + "b" * 64


def make_artifact(images = None):
    return ReleaseArtifact(
        manifest = ReleaseManifest(version = "1.4.0", infrastructure = "additive", database = "none", summary = "s"),
        commit = "0123456789abcdef",
        created_at = datetime(2026, 11, 26, tzinfo = timezone.utc),
        images = images or {"app": APP, "sandbox": SANDBOX}
    )


class TestReleaseArtifact:
    def test_it_survives_the_trip_through_yaml(self):
        artifact = make_artifact()
        assert ReleaseArtifact.from_yaml(artifact.to_yaml()) == artifact

    def test_terraform_finds_the_version_and_the_images_at_the_top_level(self):
        text = make_artifact().to_yaml()
        assert "version: 1.4.0\n" in text and f"  app: {APP}\n" in text and f"  sandbox: {SANDBOX}\n" in text

    def test_every_image_is_pinned_by_digest(self):
        with pytest.raises(ValidationError, match = "pinned by digest"):
            make_artifact({"app": "vela47-app:1.4.0", "sandbox": SANDBOX})

    def test_a_release_has_exactly_its_two_images(self):
        with pytest.raises(ValidationError):
            make_artifact({"app": APP})
