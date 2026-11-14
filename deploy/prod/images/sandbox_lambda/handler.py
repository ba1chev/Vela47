# The sandbox function: runs one command over a copy of a run's workspace and answers
# with its exit code and output. The request carries the workspace as a gzipped tar in
# base64, the command and its time limit (see SandboxLambda in app/intelligence/sandbox).
# Lambda reuses a warm environment for the next request, which can be another user's, so
# before the answer goes back every process the command started is killed and /tmp, the
# only place it could write to, is emptied, as SandboxDocker does in a container. Outside
# Lambda (a unit test) only the workspace is removed.
import io
import os
import base64
import shutil
import signal
import tarfile
import subprocess

SCRATCH = "/tmp"
WORKSPACE = "/tmp/workspace"


def _remove(path):
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path, ignore_errors = True)
    else:
        try:
            os.unlink(path)
        except OSError:
            pass


def _sweep():
    if not os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        shutil.rmtree(WORKSPACE, ignore_errors = True)
        return
    try:
        os.kill(-1, signal.SIGKILL)
    except (PermissionError, ProcessLookupError):
        pass
    for current in os.listdir(SCRATCH):
        _remove(os.path.join(SCRATCH, current))


def handler(event, context):
    timeout_seconds = int(event.get("timeout_seconds", 60))
    shutil.rmtree(WORKSPACE, ignore_errors = True)
    os.makedirs(WORKSPACE)
    try:
        with tarfile.open(fileobj = io.BytesIO(base64.b64decode(event["archive"])), mode = "r:gz") as archive:
            archive.extractall(WORKSPACE, filter = "data")
        process = subprocess.Popen(
            ["/bin/sh", "-c", event["command"]],
            cwd = WORKSPACE,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
            start_new_session = True
        )
        try:
            output, _ = process.communicate(timeout = timeout_seconds)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            return {"exit_code": -1, "output": f"Command exceeded {timeout_seconds}s and was abandoned.", "timed_out": True}
        return {"exit_code": process.returncode, "output": output.decode("utf-8", errors = "replace"), "timed_out": False}
    finally:
        _sweep()
