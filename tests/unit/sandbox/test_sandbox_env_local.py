import pytest
import pathlib
import tempfile

from app.intelligence.sandbox import SandboxEnvLocal


def make_env(name = "run"):
    return SandboxEnvLocal(pathlib.Path(tempfile.mkdtemp()) / name)


class TestSandboxEnvLocal:
    def test_starts_empty(self):
        assert make_env().list_files() == []

    def test_write_returns_relative_path(self):
        assert make_env().write_file("src/sort.py", "x = 1\n") == "src/sort.py"

    def test_write_creates_parent_directories(self):
        env = make_env()
        env.write_file("a/b/c/deep.py", "x = 1\n")
        assert env.list_files() == ["a/b/c/deep.py"]

    def test_read_returns_what_was_written(self):
        env = make_env()
        env.write_file("note.txt", "hello")
        assert env.read_file("note.txt") == "hello"

    def test_write_replaces_rather_than_appends(self):
        env = make_env()
        env.write_file("note.txt", "first")
        env.write_file("note.txt", "second")
        assert env.read_file("note.txt") == "second"

    def test_read_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            make_env().read_file("nope.txt")

    def test_list_files_is_sorted(self):
        env = make_env()
        for name in ("c.py", "a.py", "b.py"):
            env.write_file(name, "")
        assert env.list_files() == ["a.py", "b.py", "c.py"]

    def test_identifier_is_exposed(self):
        assert SandboxEnvLocal(pathlib.Path(tempfile.mkdtemp()), "slot-3").identifier == "slot-3"

    @pytest.mark.parametrize("escape", [
        "../outside.txt",
        "../../outside.txt",
        "/etc/passwd",
        "a/../../outside.txt",
        "nested/../../../outside.txt"
    ])
    def test_paths_outside_the_root_are_refused(self, escape):
        """Every path reaching a sandbox came from a model, so traversal is the
        expected input rather than an edge case."""
        env = make_env()
        with pytest.raises(ValueError):
            env.write_file(escape, "owned")

    def test_refused_path_writes_nothing(self):
        env = make_env()
        with pytest.raises(ValueError):
            env.write_file("../outside.txt", "owned")
        assert not (env.root.parent / "outside.txt").exists()

    def test_symlink_pointing_out_is_refused(self):
        env = make_env()
        outside = env.root.parent / "secret.txt"
        outside.write_text("secret")
        (env.root / "link.txt").symlink_to(outside)
        with pytest.raises(ValueError):
            env.read_file("link.txt")

    def test_oversized_file_is_not_read(self):
        env = make_env()
        env.write_file("big.txt", "x" * (SandboxEnvLocal.MAX_FILE_BYTES + 1))
        with pytest.raises(ValueError):
            env.read_file("big.txt")

    def test_oversized_file_is_not_listed(self):
        env = make_env()
        env.write_file("big.txt", "x" * (SandboxEnvLocal.MAX_FILE_BYTES + 1))
        assert env.list_files() == []

    def test_skipped_directories_are_hidden(self):
        env = make_env()
        env.write_file("__pycache__/cached.pyc", "junk")
        env.write_file("real.py", "x = 1")
        assert env.list_files() == ["real.py"]

    def test_running_a_command_is_refused(self):
        with pytest.raises(RuntimeError, match = "cannot run commands"):
            make_env().run("echo hi")
