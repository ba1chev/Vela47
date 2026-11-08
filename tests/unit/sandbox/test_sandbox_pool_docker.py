import pytest
import pathlib
import tempfile
import threading

from app.intelligence.sandbox import SandboxSlot
from app.intelligence.sandbox import SandboxPoolDocker
from app.intelligence.sandbox import SANDBOX_IMAGE_DIRECTORY
from app.intelligence.sandbox import CONTAINER_WORKSPACE_PATH


def make_context(dockerfile):
    context = pathlib.Path(tempfile.mkdtemp())
    (context / "Dockerfile").write_text(dockerfile)
    return context


def make_started_pool(size):
    pool = SandboxPoolDocker(size = size, image = "python:3.12-slim", base_directory = pathlib.Path(tempfile.mkdtemp()))
    pool._slots = [SandboxSlot(id = index, reference = f"slot-{index}") for index in range(size)]
    return pool


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

    def test_every_run_is_copied_to_the_same_workspace_from_its_own_host_directory(self):
        pool = make_started_pool(1)
        first = pool.env_for(pool._slots[0], "run-a")
        second = pool.env_for(pool._slots[0], "run-b")
        assert first.root == (pool.base_directory / "run-a").resolve() and second.root == (pool.base_directory / "run-b").resolve()
        assert first._container_directory == second._container_directory == CONTAINER_WORKSPACE_PATH

    def test_a_slot_is_not_leased_twice_until_it_is_released(self):
        pool = make_started_pool(1)
        slot = pool.acquire()
        with pytest.raises(RuntimeError, match = "No sandbox slot available"):
            pool.acquire()
        pool.release(slot)
        assert pool.acquire() == slot

    def test_threads_leasing_at_once_never_share_a_slot(self):
        pool = make_started_pool(8)
        barrier = threading.Barrier(8)
        leased = []

        def lease():
            barrier.wait()
            leased.append(pool.acquire().id)

        threads = [threading.Thread(target = lease) for _ in range(8)]
        for current_thread in threads:
            current_thread.start()
        for current_thread in threads:
            current_thread.join()
        assert sorted(leased) == list(range(8)) and pool.available == 0
