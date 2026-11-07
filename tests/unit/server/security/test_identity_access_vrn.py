from app.server.security import matches_pattern
from app.server.security import format_role_vrn
from app.server.security import format_entity_vrn
from app.server.security import IdentityEntityType
from app.server.security import IdentityAccessRoleType
from app.server.security import format_entity_type_vrn
from app.server.security import format_chat_session_vrn
from app.server.security import format_knowledge_document_vrn
from app.server.security import format_knowledge_collection_vrn
from app.server.security import format_chat_session_collection_vrn

OWN_SESSIONS = "vrn:session:${principal.id}:*"


class TestIdentityAccessVrn:
    def test_an_entity_vrn_carries_its_kind_and_id(self):
        assert format_entity_vrn(IdentityEntityType.USER, "e1") == "vrn:iam::entity/user/e1"

    def test_an_entity_type_vrn_names_the_whole_kind(self):
        assert format_entity_type_vrn(IdentityEntityType.ADMIN) == "vrn:iam::entity/admin"

    def test_a_role_vrn_names_the_role(self):
        assert format_role_vrn(IdentityAccessRoleType.GUEST) == "vrn:iam::role/guest"

    def test_a_conversation_lives_under_its_owners_collection(self):
        assert format_chat_session_collection_vrn("o1") == "vrn:session:o1:session"
        assert format_chat_session_vrn("o1", "s1") == "vrn:session:o1:session/s1"

    def test_the_own_sessions_pattern_covers_the_owners_collection_and_conversations(self):
        variables = {"principal.id": "o1"}
        assert matches_pattern(OWN_SESSIONS, format_chat_session_collection_vrn("o1"), variables)
        assert matches_pattern(OWN_SESSIONS, format_chat_session_vrn("o1", "s1"), variables)

    def test_the_own_sessions_pattern_covers_nobody_elses(self):
        variables = {"principal.id": "o1"}
        assert not matches_pattern(OWN_SESSIONS, format_chat_session_collection_vrn("o2"), variables)
        assert not matches_pattern(OWN_SESSIONS, format_chat_session_vrn("o2", "s1"), variables)

    def test_a_document_lives_under_its_owners_collection(self):
        assert format_knowledge_collection_vrn("o1") == "vrn:knowledge:o1:document"
        assert format_knowledge_document_vrn("o1", "d1") == "vrn:knowledge:o1:document/d1"

    def test_an_owner_whose_id_starts_like_another_does_not_overlap(self):
        assert not matches_pattern(OWN_SESSIONS, format_chat_session_vrn("o12", "s1"), {"principal.id": "o1"})
