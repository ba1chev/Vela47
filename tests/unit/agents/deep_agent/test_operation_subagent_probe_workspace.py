import pathlib
import tempfile

from app.intelligence.sandbox import SandboxEnvLocal
from app.intelligence.agents import OperationSubagentProbeWorkspace


def make_probe(files = None):
    env = SandboxEnvLocal(pathlib.Path(tempfile.mkdtemp()) / "run")
    for current_path, current_content in (files or {}).items():
        env.write_file(current_path, current_content)
    return OperationSubagentProbeWorkspace(env), env


class TestOperationSubagentProbeWorkspace:
    def test_a_file_written_during_the_step_is_reported_with_its_lines(self):
        probe, env = make_probe()
        probe.before()
        env.write_file("primes.py", "def is_prime(n):\n    return n > 1\n")
        assert probe.after([]) == ["Files created: primes.py (2 lines)."]

    def test_files_from_an_earlier_step_are_not_reported_again(self):
        probe, env = make_probe({"old.py": "x = 1\n"})
        probe.before()
        env.write_file("new.py", "y = 2\n")
        assert probe.after([]) == ["Files created: new.py (1 line)."]

    def test_a_changed_file_is_reported_as_changed(self):
        probe, env = make_probe({"a.py": "x = 1\n"})
        probe.before()
        env.write_file("a.py", "x = 2\ny = 3\n")
        assert probe.after([]) == ["Files changed: a.py (2 lines)."]

    def test_a_step_that_wrote_nothing_says_so(self):
        probe, _ = make_probe({"a.py": "x = 1\n"})
        probe.before()
        assert probe.after([]) == ["No file in the workspace was created or changed in this step."]

    def test_a_long_list_ends_with_how_many_more(self):
        probe, env = make_probe()
        probe.before()
        for index in range(12):
            env.write_file(f"f{index:02d}.py", "x\n")
        fact = probe.after([])[0]
        assert fact.endswith("and 2 more.") and "f09.py" in fact and "f10.py" not in fact
