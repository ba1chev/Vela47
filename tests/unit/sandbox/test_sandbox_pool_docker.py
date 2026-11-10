import re
import pytest
import pathlib
import tempfile
import threading

from app.intelligence.sandbox import SandboxSlot
from app.intelligence.sandbox import SandboxPoolDocker
from app.intelligence.sandbox import SANDBOX_COMPOSE_FILE
from app.intelligence.sandbox import SANDBOX_IMAGE_DIRECTORY
from app.intelligence.sandbox import CONTAINER_WORKSPACE_PATH


def make_pool():
    return SandboxPoolDocker(base_directory = pathlib.Path(tempfile.mkdtemp()))


def make_started_pool(size):
    pool = make_pool()
    pool._slots = [SandboxSlot(id = index, reference = f"vela47-slot-{index}") for index in range(size)]
    return pool


class TestSandboxPoolDocker:
    def test_the_bundled_image_has_pytest_for_the_test_subagent(self):
        assert "pytest" in (SANDBOX_IMAGE_DIRECTORY / "Dockerfile").read_text()

    def test_the_bundled_network_reaches_nothing(self):
        compose = SANDBOX_COMPOSE_FILE.read_text()
        assert "internal: true" in compose
        assert "gateway_mode_ipv4: isolated" in compose
        assert 'enable_icc: "false"' in compose

    def test_every_bundled_slot_has_a_name_and_an_address_of_its_own(self):
        compose = SANDBOX_COMPOSE_FILE.read_text()
        names = re.findall(r"container_name: (\S+)", compose)
        addresses = re.findall(r"ipv4_address: (\S+)", compose)
        assert len(names) == len(set(names)) == len(addresses) == len(set(addresses)) == 10

    def test_slots_are_the_compose_services_in_a_stable_order(self):
        slots = make_pool()._slots_from({"services": {
            "slot-1": {"container_name": "vela47-slot-1"},
            "slot-0": {"container_name": "vela47-slot-0"}
        }})
        assert slots == [SandboxSlot(id = 0, reference = "vela47-slot-0"), SandboxSlot(id = 1, reference = "vela47-slot-1")]

    def test_a_service_without_a_container_name_is_refused(self):
        with pytest.raises(RuntimeError, match = "slot-1 has none"):
            make_pool()._slots_from({"services": {"slot-0": {"container_name": "vela47-slot-0"}, "slot-1": {}}})

    def test_a_compose_file_without_services_is_refused(self):
        with pytest.raises(RuntimeError, match = "defines no service"):
            make_pool()._slots_from({"services": {}})

    def test_a_slot_is_entered_by_its_container_name(self):
        pool = make_started_pool(2)
        assert pool.env_for(pool._slots[1], "run-a").identifier == "vela47-slot-1"

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
