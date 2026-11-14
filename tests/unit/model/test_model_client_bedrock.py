import pytest
from botocore.exceptions import ClientError

from app.intelligence.model import ModelConfig
from app.intelligence.messages import MessageAI
from app.intelligence.messages import MessageTool
from app.intelligence.messages import MessageHuman
from app.intelligence.model import ModelClientType
from app.intelligence.messages import MessageSystem
from app.intelligence.messages import MessageToolCall
from app.intelligence.model import ModelClientBedrock
from tests.fixtures.model.stub_bedrock_runtime import StubBedrockRuntime

TOOLS = [{"type": "function", "function": {"name": "read_file", "description": "Read a file.",
    "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}}}]


def make_client(**stub_fields):
    runtime = StubBedrockRuntime(**stub_fields)
    return ModelClientBedrock("eu-central-1", runtime = runtime), runtime


def make_config(**fields):
    return ModelConfig(model_name = "qwen.qwen3-235b-a22b-2507-v1:0", **fields)


def call(name, id, args = None):
    return MessageAI(content = "", tool_calls = [MessageToolCall(name = name, args = args or {"path": "a.py"}, id = id)])


def result(id, content = "1  x", status = "success"):
    return MessageTool(content = content, tool_call_id = id, name = "read_file", status = status)


def sent(messages, tools = None, **config_fields):
    client, runtime = make_client()
    client.chat(make_config(**config_fields), messages, tools)
    return runtime.requests[0]


class TestModelClientBedrock:
    def test_it_is_the_bedrock_type(self):
        assert make_client()[0].client_type is ModelClientType.BEDROCK

    def test_system_messages_go_to_the_system_field(self):
        request = sent([MessageSystem(content = "rules"), MessageHuman(content = "hi")])
        assert request["system"] == [{"text": "rules"}]
        assert request["messages"] == [{"role": "user", "content": [{"text": "hi"}]}]

    def test_the_model_and_its_sampling_are_sent(self):
        request = sent([MessageHuman(content = "hi")], temperature = 0.1, top_p = 0.8, max_output_tokens = 512, stop = ["END"])
        assert request["modelId"] == "qwen.qwen3-235b-a22b-2507-v1:0"
        assert request["inferenceConfig"] == {"temperature": 0.1, "maxTokens": 512, "stopSequences": ["END"]}

    def test_a_conversation_that_starts_with_the_assistant_gets_a_user_turn_first(self):
        request = sent([MessageAI(content = "earlier answer"), MessageHuman(content = "and now?")])
        assert [current["role"] for current in request["messages"]] == ["user", "assistant", "user"]

    def test_turns_of_one_role_are_merged(self):
        request = sent([MessageHuman(content = "one"), MessageHuman(content = "two")])
        assert request["messages"] == [{"role": "user", "content": [{"text": "one"}, {"text": "two"}]}]

    def test_a_call_and_its_results_travel_as_tool_blocks_with_the_tools(self):
        two_calls = MessageAI(content = "", tool_calls = [
            MessageToolCall(name = "read_file", args = {"path": "a.py"}, id = "c1"),
            MessageToolCall(name = "read_file", args = {"path": "b.py"}, id = "c2")
        ])
        request = sent([MessageHuman(content = "read both"), two_calls, result("c1"), result("c2", "boom", "error")], TOOLS)
        assistant, results = request["messages"][1], request["messages"][2]
        assert [block["toolUse"]["toolUseId"] for block in assistant["content"]] == ["c1", "c2"]
        assert results == {"role": "user", "content": [
            {"toolResult": {"toolUseId": "c1", "content": [{"text": "1  x"}], "status": "success"}},
            {"toolResult": {"toolUseId": "c2", "content": [{"text": "boom"}], "status": "error"}}
        ]}
        assert request["toolConfig"]["tools"][0]["toolSpec"] == {
            "name": "read_file", "description": "Read a file.", "inputSchema": {"json": TOOLS[0]["function"]["parameters"]}
        }

    def test_without_tools_every_tool_block_becomes_text(self):
        request = sent([MessageHuman(content = "go"), call("read_file", "c1"), result("c1"), MessageHuman(content = "report now")])
        assert "toolConfig" not in request
        assert request["messages"][1]["content"] == [{"text": '(called read_file with {"path": "a.py"})'}]
        assert request["messages"][2]["content"] == [{"text": "(result of read_file: 1  x)"}, {"text": "report now"}]

    def test_a_result_whose_call_was_cut_away_becomes_text(self):
        request = sent([MessageHuman(content = "go"), result("gone"), MessageHuman(content = "next")], TOOLS)
        assert request["messages"][0]["content"][1] == {"text": "(result of read_file: 1  x)"}

    def test_a_call_that_was_never_answered_becomes_text(self):
        request = sent([MessageHuman(content = "go"), call("read_file", "c1"), MessageHuman(content = "next")], TOOLS)
        assert request["messages"][1]["content"] == [{"text": '(called read_file with {"path": "a.py"})'}]

    def test_a_call_without_an_id_becomes_text(self):
        request = sent([MessageHuman(content = "go"), call("read_file", None), result("")], TOOLS)
        assert request["messages"][1]["content"][0]["text"].startswith("(called read_file")
        assert request["messages"][2]["content"][0]["text"].startswith("(result of read_file")

    def test_an_empty_turn_still_says_something(self):
        request = sent([MessageHuman(content = "hi"), MessageAI(content = ""), MessageHuman(content = "again")])
        assert request["messages"][1] == {"role": "assistant", "content": [{"text": "(empty)"}]}

    def test_the_reply_carries_its_text_calls_and_usage(self):
        client, _ = make_client(replies = [[{"text": "Reading. "}, {"toolUse": {"toolUseId": "t9", "name": "read_file", "input": {"path": "a.py"}}}]])
        reply = client.chat(make_config(), [MessageHuman(content = "read a.py")], TOOLS)
        assert reply.content == "Reading. "
        assert [(current.name, current.args, current.id) for current in reply.tool_calls] == [("read_file", {"path": "a.py"}, "t9")]
        assert (reply.usage_metadata.input_tokens, reply.usage_metadata.output_tokens) == (11, 3)

    def test_an_output_schema_constrains_the_reply(self):
        client, runtime = make_client()
        client.chat(make_config(), [MessageHuman(content = "plan")], output_schema = {"type": "object"})
        assert runtime.requests[0]["outputConfig"]["textFormat"]["type"] == "json_schema"
        assert runtime.requests[0]["outputConfig"]["textFormat"]["structure"]["jsonSchema"]["schema"] == '{"type": "object"}'

    def test_a_model_without_structured_output_is_asked_again_and_remembered(self):
        client, runtime = make_client(reject_output_format = True)
        client.chat(make_config(), [MessageHuman(content = "plan")], output_schema = {"type": "object"})
        client.chat(make_config(), [MessageHuman(content = "plan")], output_schema = {"type": "object"})
        assert ["outputConfig" in current for current in runtime.requests] == [True, False, False]

    def test_other_errors_are_not_swallowed(self):
        client, _ = make_client(error = "ThrottlingException")
        with pytest.raises(ClientError):
            client.chat(make_config(), [MessageHuman(content = "hi")], output_schema = {"type": "object"})

    def test_a_stream_yields_text_then_the_usage(self):
        events = [{"messageStart": {"role": "assistant"}}, {"contentBlockDelta": {"delta": {"text": "Hel"}}},
            {"contentBlockDelta": {"delta": {"text": "lo"}}}, {"messageStop": {}}, {"metadata": {"usage": {"inputTokens": 4, "outputTokens": 2}}}]
        client, runtime = make_client(stream_events = events)
        pieces = list(client.stream(make_config(), [MessageHuman(content = "hi")]))
        assert [current.content for current in pieces] == ["Hel", "lo", ""]
        assert pieces[-1].usage_metadata.total_tokens == 6 and "toolConfig" not in runtime.requests[0]

    def test_every_text_is_embedded_in_order_with_its_tokens(self):
        client, runtime = make_client()
        vectors, tokens = client.embed("amazon.titan-embed-text-v2:0", ["a", "bb ccc", "dddd"], "30m")
        assert vectors == [[1.0, 1.0], [6.0, 1.0], [4.0, 1.0]] and tokens == 4
        assert sorted(text for _, text in runtime.embedded) == ["a", "bb ccc", "dddd"]
