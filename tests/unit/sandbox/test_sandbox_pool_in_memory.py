import pytest
import pathlib
import tempfile

from app.intelligence.sandbox import SandboxPoolInMemory


def make_pool(size = 3):
    return SandboxPoolInMemory(size = size, base_directory = pathlib.Path(tempfile.mkdtemp()))


class TestSandboxPoolInMemory:
    def test_starts_with_every_slot_free(self):
        assert make_pool(3).available == 3

    def test_acquire_reduces_availability(self):
        pool = make_pool(3)
        pool.acquire()
        assert pool.available == 2

    def test_release_restores_availability(self):
        pool = make_pool(2)
        slot = pool.acquire()
        pool.release(slot)
        assert pool.available == 2

    def test_acquire_hands_out_distinct_slots(self):
        pool = make_pool(3)
        assert len({pool.acquire().id for _ in range(3)}) == 3

    def test_exhausted_pool_raises_rather_than_waiting(self):
        """Blocking would hide over-subscription as a hang; raising lets the layer
        report it as a failed task."""
        pool = make_pool(1)
        pool.acquire()
        with pytest.raises(RuntimeError, match = "No sandbox slot available"):
            pool.acquire()

    def test_releasing_a_free_slot_is_safe(self):
        """Callers release from a finally block, which can run twice."""
        pool = make_pool(2)
        slot = pool.acquire()
        pool.release(slot)
        pool.release(slot)
        assert pool.available == 2

    def test_env_is_scoped_to_the_run_not_the_slot(self):
        """A file written through one lease must still be there for the next, or a
        CODE subagent's work would vanish before REVIEW could read it."""
        pool = make_pool(2)
        first, second = pool.acquire(), pool.acquire()
        pool.env_for(first, "RUN").write_file("note.txt", "from the first slot")
        assert pool.env_for(second, "RUN").read_file("note.txt") == "from the first slot"

    def test_different_runs_do_not_share_files(self):
        pool = make_pool(2)
        slot = pool.acquire()
        pool.env_for(slot, "RUN_A").write_file("note.txt", "a")
        assert pool.env_for(slot, "RUN_B").list_files() == []

    def test_len_reports_pool_size(self):
        assert len(make_pool(5)) == 5

    def test_lifecycle_hooks_are_safe_to_call(self):
        """The base implementations do nothing; a caller should not have to know that."""
        pool = make_pool(1)
        pool.start()
        pool.shutdown()
        assert pool.available == 1
