import time
import pytest
import pathlib
import tempfile

from db import DatabaseSqlite
from app.intelligence.messages import MessageAI
from app.server.chat_sessions import ChatSession
from app.intelligence.messages import MessageTool
from app.intelligence.messages import MessageHuman
from app.intelligence.messages import MessageToolCall
from app.server.chat_sessions import ChatSessionStoreSql
from app.intelligence.messages import MessageUsageMetadata


def make_store(path = None):
    database = DatabaseSqlite(path)
    database.start()
    return ChatSessionStoreSql(database)


def make_session(owner_id = "o1", **fields):
    return ChatSession(owner_id = owner_id, **fields)


class TestChatSessionStoreSql:
    def test_a_session_reads_back_equal_to_what_was_stored(self):
        store = make_store()
        session = make_session(title = "Sorting", messages = [MessageHuman(content = "sort this")])
        store.create_session(session)
        assert store.get_session(session.id) == session

    def test_creating_the_same_id_twice_is_refused(self):
        store = make_store()
        session = make_session()
        store.create_session(session)
        with pytest.raises(ValueError):
            store.create_session(session)

    def test_an_unknown_session_reads_as_none(self):
        assert make_store().get_session("missing") is None

    def test_appended_messages_come_back_as_their_own_classes(self):
        store = make_store()
        session = make_session(messages = [MessageHuman(content = "hi")])
        store.create_session(session)
        appended = store.append_messages(session.id, [MessageAI(content = "hello")])
        assert [type(current).__name__ for current in appended.messages] == ["MessageHuman", "MessageAI"]
        assert store.get_session(session.id) == appended

    def test_ai_tool_calls_and_usage_survive_storage(self):
        store = make_store()
        session = make_session()
        store.create_session(session)
        message = MessageAI(
            content = "done",
            tool_calls = [MessageToolCall(name = "write_file", args = {"path": "a.py"}, id = "c1")],
            usage_metadata = MessageUsageMetadata(input_tokens = 3, output_tokens = 4, total_tokens = 7)
        )
        stored = store.append_messages(session.id, [message]).messages[0]
        assert stored.tool_calls[0].args == {"path": "a.py"}
        assert stored.usage_metadata.total_tokens == 7

    def test_a_tool_artifact_is_never_stored(self):
        store = make_store()
        session = make_session()
        store.create_session(session)
        stored = store.append_messages(
            session.id, [MessageTool(content = "ok", tool_call_id = "c1", artifact = object())]
        ).messages[0]
        assert stored.artifact is None and stored.tool_call_id == "c1"

    def test_appending_moves_updated_at_forward(self):
        store = make_store()
        session = make_session()
        store.create_session(session)
        assert store.append_messages(session.id, [MessageHuman(content = "x")]).updated_at > session.updated_at

    def test_appending_to_an_unknown_session_raises_key_error(self):
        with pytest.raises(KeyError):
            make_store().append_messages("missing", [MessageHuman(content = "x")])

    def test_an_owner_sees_only_their_own_sessions(self):
        store = make_store()
        mine = make_session("me")
        store.create_session(mine)
        store.create_session(make_session("someone-else"))
        assert [current.id for current in store.list_sessions("me")] == [mine.id]

    def test_sessions_are_listed_most_recently_updated_first(self):
        store = make_store()
        older, newer = make_session(), make_session()
        store.create_session(older)
        store.create_session(newer)
        time.sleep(0.01)
        store.append_messages(older.id, [MessageHuman(content = "bump")])
        assert [current.id for current in store.list_sessions("o1")] == [older.id, newer.id]

    def test_delete_reports_whether_there_was_anything_to_delete(self):
        store = make_store()
        session = make_session()
        store.create_session(session)
        assert store.delete_session(session.id) is True
        assert store.delete_session(session.id) is False
        assert store.get_session(session.id) is None

    def test_conversations_survive_a_restart(self):
        path = pathlib.Path(tempfile.mkdtemp()) / "vela47.sqlite3"
        session = make_session(messages = [MessageHuman(content = "remember me")])
        make_store(path).create_session(session)
        assert make_store(path).get_session(session.id) == session
