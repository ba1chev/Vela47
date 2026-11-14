import io
import json
import base64
import tarfile


class StubLambdaClient:
    """Stands in for the boto3 Lambda client: unpacks every request the way the sandbox
    function would and answers from a script, so what SandboxLambda sends and how it
    reads the reply can be checked without AWS. failure makes the function report an
    error, unreachable makes the call itself raise."""

    def __init__(self, answer = None, failure = None, unreachable = False) -> None:
        self.requests = []
        self._answer = answer or {"exit_code": 0, "output": "1 passed", "timed_out": False}
        self._failure = failure
        self._unreachable = unreachable

    def invoke(self, FunctionName, Payload):
        if self._unreachable:
            raise ConnectionError("no route to Lambda")
        request = json.loads(Payload)
        with tarfile.open(fileobj = io.BytesIO(base64.b64decode(request["archive"])), mode = "r:gz") as archive:
            files = {member.name: archive.extractfile(member).read().decode() for member in archive.getmembers() if member.isfile()}
        self.requests.append({"function": FunctionName, "command": request["command"], "timeout_seconds": request["timeout_seconds"], "files": files})
        if self._failure is not None:
            return {"FunctionError": "Unhandled", "Payload": io.BytesIO(json.dumps({"errorMessage": self._failure}).encode())}
        return {"Payload": io.BytesIO(json.dumps(self._answer).encode())}
