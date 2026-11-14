import pytest
import pathlib
import tempfile

from app.intelligence.sandbox import SandboxLambda
from app.intelligence.sandbox import SandboxPoolLambda
from tests.fixtures.sandbox.stub_lambda_client import StubLambdaClient


def make_pool(size = 2):
    return SandboxPoolLambda("vela47-sandbox", "eu-central-1", size, pathlib.Path(tempfile.mkdtemp()), StubLambdaClient())


class TestSandboxPoolLambda:
    def test_every_slot_names_the_function(self):
        pool = make_pool()
        assert pool.acquire().reference == "vela47-sandbox"

    def test_it_holds_its_size_and_refuses_beyond_it(self):
        pool = make_pool(2)
        pool.acquire(), pool.acquire()
        with pytest.raises(RuntimeError, match = "No sandbox slot available"):
            pool.acquire()

    def test_a_released_slot_can_be_taken_again(self):
        pool = make_pool(1)
        slot = pool.acquire()
        pool.release(slot)
        assert pool.available == 1 and pool.acquire().id == slot.id

    def test_a_slot_runs_on_the_runs_directory_under_the_pool(self):
        pool = make_pool()
        env = pool.env_for(pool.acquire(), "run-a")
        assert isinstance(env, SandboxLambda) and env.root == (pool.base_directory / "run-a").resolve()

    def test_starting_and_stopping_need_nothing(self):
        pool = make_pool()
        pool.start(), pool.shutdown()
        assert pool.available == 2
