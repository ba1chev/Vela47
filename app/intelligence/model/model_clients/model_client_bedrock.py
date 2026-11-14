import json
import boto3
from botocore.config import Config
from typing import Any, Iterator, Optional
from botocore.exceptions import ClientError
from concurrent.futures import ThreadPoolExecutor

from app.intelligence.model import ModelConfig
from app.intelligence.messages import MessageAI
from app.intelligence.messages import MessageTool
from app.intelligence.messages import MessageType
from app.intelligence.messages import MessageBase
from app.intelligence.model import ModelClientType
from app.intelligence.model import ModelClientBase
from app.intelligence.messages import MessageToolCall
from app.intelligence.messages import MessageUsageMetadata


class ModelClientBedrock(ModelClientBase):
    """Amazon Bedrock through the Converse API, authorised by the IAM role of whatever
    runs it. Converse is stricter than Ollama: a conversation starts with the user, roles
    alternate, a tool result answers a call of the turn before, and tool blocks need the
    tools. A sliding window or a final turn without tools breaks each of those, so the
    history is mended here: turns of one role are merged, tool blocks without their
    counterpart become text, and a request without tools gets them all as text.

    An output_schema becomes a JSON schema output format; a model that rejects it is
    asked again without one, and remembered. Sampling beyond temperature, top_p, stop and
    the output cap has no Converse field and is left out. Embeddings use the Titan Text
    Embeddings body, one text per request, several requests at a time."""

    EMBEDDING_WORKERS = 8
    EMPTY_TEXT = "(empty)"

    def __init__(self, region_name: str, runtime: Optional[Any] = None) -> None:
        self._runtime: Any = runtime if runtime is not None else boto3.client(
            "bedrock-runtime",
            region_name = region_name,
            config = Config(retries = {"mode": "standard", "max_attempts": 5}, read_timeout = 300)
        )
        self._without_output_format: set[str] = set()

    @property
    def client_type(self) -> ModelClientType:
        return ModelClientType.BEDROCK

    def _text_of(self, message: MessageBase) -> str:
        return message.content if isinstance(message.content, str) else str(message.content)

    def _blocks(self, message: MessageBase) -> list[dict]:
        text = self._text_of(message)
        if isinstance(message, MessageTool):
            block = {"toolResult": {
                "toolUseId": message.tool_call_id,
                "content": [{"text": text or self.EMPTY_TEXT}],
                "status": "error" if message.status == "error" else "success"
            }, "name": message.name or "tool"}
            return [block if message.tool_call_id else self._as_text(block)]
        blocks = [{"text": text}] if text.strip() else []
        if isinstance(message, MessageAI):
            for current_call in message.tool_calls:
                block = {"toolUse": {"toolUseId": current_call.id, "name": current_call.name, "input": current_call.args}}
                blocks.append(block if current_call.id else self._as_text(block))
        return blocks

    def _as_text(self, block: dict) -> dict:
        if "toolUse" in block:
            call = block["toolUse"]
            return {"text": f"(called {call['name']} with {json.dumps(call['input'], ensure_ascii = False)})"}
        if "toolResult" in block:
            return {"text": f"(result of {block['name']}: {block['toolResult']['content'][0]['text']})"}
        return block

    def _mend(self, turns: list[dict], with_tools: bool) -> list[dict]:
        for index, current_turn in enumerate(turns):
            previous = turns[index - 1]["content"] if index > 0 else []
            following = turns[index + 1]["content"] if index + 1 < len(turns) else []
            called = {block["toolUse"]["toolUseId"] for block in previous if "toolUse" in block}
            answered = {block["toolResult"]["toolUseId"] for block in following if "toolResult" in block}
            current_turn["content"] = [
                self._as_text(block)
                if not with_tools
                or ("toolResult" in block and block["toolResult"]["toolUseId"] not in called)
                or ("toolUse" in block and block["toolUse"]["toolUseId"] not in answered)
                else block
                for block in current_turn["content"]
            ]
        for current_turn in turns:
            for block in current_turn["content"]:
                block.pop("name", None)
            current_turn["content"] = [
                block for block in current_turn["content"] if "text" not in block or block["text"].strip()
            ] or [{"text": self.EMPTY_TEXT}]
        return turns

    def _conversation(self, messages: list[MessageBase], with_tools: bool) -> tuple[list[dict], list[dict]]:
        system = [{"text": self._text_of(current)} for current in messages
            if current.type is MessageType.SYSTEM_MESSAGE and self._text_of(current).strip()]
        turns: list[dict] = []
        for current in messages:
            if current.type is MessageType.SYSTEM_MESSAGE:
                continue
            role = "assistant" if current.type is MessageType.AI_MESSAGE else "user"
            blocks = self._blocks(current)
            if turns and turns[-1]["role"] == role:
                turns[-1]["content"].extend(blocks)
            else:
                turns.append({"role": role, "content": blocks})
        if not turns or turns[0]["role"] != "user":
            turns.insert(0, {"role": "user", "content": [{"text": "(the conversation so far)"}]})
        return system, self._mend(turns, with_tools)

    def _tool_config(self, tools: list[dict]) -> dict:
        return {"tools": [
            {"toolSpec": {
                "name": current["function"]["name"],
                "description": current["function"].get("description", ""),
                "inputSchema": {"json": current["function"].get("parameters", {"type": "object"})}
            }}
            for current in tools
        ]}

    def _request(self, config: ModelConfig, messages: list[MessageBase],
        tools: Optional[list[dict]] = None) -> dict:
        system, conversation = self._conversation(messages, bool(tools))
        inference: dict = {"temperature": config.temperature, "topP": config.top_p}
        if config.max_output_tokens is not None:
            inference["maxTokens"] = config.max_output_tokens
        if config.stop:
            inference["stopSequences"] = config.stop
        request: dict = {"modelId": config.model_name, "messages": conversation, "inferenceConfig": inference}
        if system:
            request["system"] = system
        if tools:
            request["toolConfig"] = self._tool_config(tools)
        return request

    def _usage(self, usage: dict) -> MessageUsageMetadata:
        input_tokens, output_tokens = usage.get("inputTokens", 0), usage.get("outputTokens", 0)
        return MessageUsageMetadata(
            input_tokens = input_tokens,
            output_tokens = output_tokens,
            total_tokens = input_tokens + output_tokens
        )

    def _converse(self, request: dict, output_schema: Optional[dict]) -> dict:
        if output_schema is None or request["modelId"] in self._without_output_format:
            return self._runtime.converse(**request)
        try:
            return self._runtime.converse(**request, outputConfig = {"textFormat": {
                "type": "json_schema",
                "structure": {"jsonSchema": {"schema": json.dumps(output_schema), "name": "reply"}}
            }})
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") != "ValidationException":
                raise
            self._without_output_format.add(request["modelId"])
            return self._runtime.converse(**request)

    def chat(self, config: ModelConfig, messages: list[MessageBase], tools: Optional[list[dict]] = None,
        output_schema: Optional[dict] = None) -> MessageAI:
        response = self._converse(self._request(config, messages, tools), output_schema)
        blocks = response["output"]["message"]["content"]
        return MessageAI(
            content = "".join(block["text"] for block in blocks if "text" in block),
            tool_calls = [
                MessageToolCall(name = block["toolUse"]["name"], args = block["toolUse"].get("input") or {},
                    id = block["toolUse"]["toolUseId"])
                for block in blocks if "toolUse" in block
            ],
            usage_metadata = self._usage(response.get("usage", {}))
        )

    def stream(self, config: ModelConfig, messages: list[MessageBase]) -> Iterator[MessageAI]:
        usage: dict = {}
        for event in self._runtime.converse_stream(**self._request(config, messages))["stream"]:
            text = event.get("contentBlockDelta", {}).get("delta", {}).get("text")
            if text:
                yield MessageAI(content = text)
            usage = event.get("metadata", {}).get("usage", usage)
        yield MessageAI(content = "", usage_metadata = self._usage(usage))

    def _embed_one(self, model_name: str, text: str) -> tuple[list[float], int]:
        response = self._runtime.invoke_model(
            modelId = model_name,
            body = json.dumps({"inputText": text}),
            contentType = "application/json",
            accept = "application/json"
        )
        body = json.loads(response["body"].read())
        return list(body["embedding"]), body.get("inputTextTokenCount", 0)

    def embed(self, model_name: str, texts: list[str], keep_alive: str) -> tuple[list[list[float]], int]:
        with ThreadPoolExecutor(max_workers = self.EMBEDDING_WORKERS) as executor:
            results = list(executor.map(lambda current: self._embed_one(model_name, current), texts))
        return [vector for vector, _ in results], sum(tokens for _, tokens in results)
