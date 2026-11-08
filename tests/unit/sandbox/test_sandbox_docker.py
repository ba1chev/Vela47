import io
import pathlib
import tarfile
import tempfile

from app.intelligence.sandbox import SandboxDocker
from app.intelligence.sandbox import CONTAINER_WORKSPACE_PATH


def make_env(base = None, run_id = "run-a"):
    return SandboxDocker("vela47-slot-0", (base or pathlib.Path(tempfile.mkdtemp())) / run_id, CONTAINER_WORKSPACE_PATH)


def archived_files(env):
    with tarfile.open(fileobj = io.BytesIO(env._archive())) as archive:
        return {
            current.name: archive.extractfile(current).read().decode("utf-8")
            for current in archive.getmembers()
            if current.isfile()
        }


class TestSandboxDocker:
    def test_the_copy_holds_the_runs_files_at_their_workspace_paths(self):
        env = make_env()
        env.write_file("sort.py", "def sort(items):\n    return sorted(items)\n")
        env.write_file("tests/test_sort.py", "from sort import sort\n")
        assert archived_files(env) == {
            "./sort.py": "def sort(items):\n    return sorted(items)\n",
            "./tests/test_sort.py": "from sort import sort\n"
        }

    def test_the_copy_holds_nothing_from_another_run(self):
        base = pathlib.Path(tempfile.mkdtemp())
        make_env(base, "run-a").write_file("secret.py", "TOKEN = 'a'\n")
        other = make_env(base, "run-b")
        other.write_file("main.py", "x = 1\n")
        assert list(archived_files(other)) == ["./main.py"]

    def test_an_empty_run_is_copied_as_an_empty_workspace(self):
        assert archived_files(make_env()) == {}

    def test_file_operations_stay_on_the_host(self):
        env = make_env()
        env.write_file("notes.md", "hello")
        assert (env.root / "notes.md").read_text() == "hello" and env.list_files() == ["notes.md"]
