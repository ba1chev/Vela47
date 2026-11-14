import io
import base64
import pathlib
import tarfile
import tempfile
import importlib.util

HANDLER_PATH = pathlib.Path(__file__).resolve().parents[3] / "deploy" / "prod" / "images" / "sandbox_lambda" / "handler.py"


def load_handler():
    spec = importlib.util.spec_from_file_location("sandbox_lambda_handler", HANDLER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.WORKSPACE = str(pathlib.Path(tempfile.mkdtemp()) / "workspace")
    return module


def make_event(files, command, timeout_seconds = 10):
    buffer = io.BytesIO()
    with tarfile.open(fileobj = buffer, mode = "w:gz") as archive:
        for name, content in files.items():
            data = content.encode()
            info = tarfile.TarInfo(name = f"./{name}")
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return {"archive": base64.b64encode(buffer.getvalue()).decode(), "command": command, "timeout_seconds": timeout_seconds}


class TestSandboxLambdaHandler:
    def test_the_command_runs_over_the_workspace_it_was_sent(self):
        module = load_handler()
        answer = module.handler(make_event({"a.txt": "hello"}, "cat a.txt; echo; exit 3"), None)
        assert answer == {"exit_code": 3, "output": "hello\n", "timed_out": False}

    def test_errors_are_part_of_the_output(self):
        answer = load_handler().handler(make_event({}, "echo out; echo err >&2"), None)
        assert answer["output"] == "out\nerr\n"

    def test_a_command_past_its_limit_is_abandoned(self):
        answer = load_handler().handler(make_event({}, "sleep 5", timeout_seconds = 1), None)
        assert answer["timed_out"] and answer["exit_code"] == -1

    def test_the_workspace_is_gone_once_it_answers(self):
        module = load_handler()
        module.handler(make_event({"a.txt": "x"}, "true"), None)
        assert not pathlib.Path(module.WORKSPACE).exists()

    def test_nothing_from_an_earlier_request_is_left(self):
        module = load_handler()
        module.handler(make_event({"first.txt": "x"}, "true"), None)
        assert module.handler(make_event({"second.txt": "y"}, "ls"), None)["output"] == "second.txt\n"

    def test_a_path_out_of_the_workspace_is_not_extracted(self):
        module = load_handler()
        buffer = io.BytesIO()
        with tarfile.open(fileobj = buffer, mode = "w:gz") as archive:
            info = tarfile.TarInfo(name = "../escaped.txt")
            info.size = 1
            archive.addfile(info, io.BytesIO(b"x"))
        event = {"archive": base64.b64encode(buffer.getvalue()).decode(), "command": "true", "timeout_seconds": 5}
        try:
            module.handler(event, None)
        except tarfile.TarError:
            pass
        assert not (pathlib.Path(module.WORKSPACE).parent / "escaped.txt").exists()
