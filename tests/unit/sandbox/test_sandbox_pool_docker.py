import pytest
import pathlib
import tempfile

from app.intelligence.sandbox import SandboxPoolDocker
from app.intelligence.sandbox import SANDBOX_IMAGE_DIRECTORY


def make_context(dockerfile):
    context = pathlib.Path(tempfile.mkdtemp())
    (context / "Dockerfile").write_text(dockerfile)
    return context


class TestSandboxPoolDocker:
    def test_by_default_the_bundled_image_is_built_and_tagged_by_its_contents(self):
        pool = SandboxPoolDocker(size = 1)
        assert pool.image.startswith("vela47-sandbox:") and pool._build_context == SANDBOX_IMAGE_DIRECTORY

    def test_the_bundled_image_has_pytest_for_the_test_subagent(self):
        assert "pytest" in (SANDBOX_IMAGE_DIRECTORY / "Dockerfile").read_text()

    def test_changing_the_dockerfile_changes_the_tag(self):
        first = SandboxPoolDocker(size = 1, build_context = make_context("FROM python:3.12-slim\n"))
        second = SandboxPoolDocker(size = 1, build_context = make_context("FROM python:3.13-slim\n"))
        assert first.image != second.image

    def test_a_named_image_is_pulled_rather_than_built(self):
        pool = SandboxPoolDocker(size = 1, image = "python:3.12-slim")
        assert pool.image == "python:3.12-slim" and pool._build_context is None

    def test_a_pool_with_neither_an_image_nor_a_build_context_is_refused(self):
        with pytest.raises(ValueError, match = "image to pull or a build context"):
            SandboxPoolDocker(size = 1, image = None, build_context = None)
