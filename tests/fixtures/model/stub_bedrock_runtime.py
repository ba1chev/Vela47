import io
import json
from botocore.exceptions import ClientError


class StubBedrockRuntime:
    """Stands in for the boto3 bedrock-runtime client: records every request and answers
    from a script, so what ModelClientBedrock sends to Converse can be checked without
    AWS. reject_output_format makes a request with an outputConfig fail validation, like
    a model without structured output; error makes every converse call fail with it."""

    def __init__(self, replies = None, stream_events = None, reject_output_format = False, error = None) -> None:
        self.requests = []
        self.embedded = []
        self._replies = list(replies or [])
        self._stream_events = list(stream_events or [])
        self._reject_output_format = reject_output_format
        self._error = error

    def converse(self, **request):
        self.requests.append(request)
        if self._error is not None:
            raise ClientError({"Error": {"Code": self._error, "Message": "boom"}}, "Converse")
        if self._reject_output_format and "outputConfig" in request:
            raise ClientError({"Error": {"Code": "ValidationException", "Message": "outputConfig is not supported"}}, "Converse")
        content = self._replies.pop(0) if self._replies else [{"text": "done"}]
        return {"output": {"message": {"role": "assistant", "content": content}}, "usage": {"inputTokens": 11, "outputTokens": 3}}

    def converse_stream(self, **request):
        self.requests.append(request)
        return {"stream": iter(self._stream_events)}

    def invoke_model(self, **request):
        text = json.loads(request["body"])["inputText"]
        self.embedded.append((request["modelId"], text))
        body = {"embedding": [float(len(text)), 1.0], "inputTextTokenCount": len(text.split())}
        return {"body": io.BytesIO(json.dumps(body).encode())}
