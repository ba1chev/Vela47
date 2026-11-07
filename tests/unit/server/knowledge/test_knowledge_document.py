import pytest
from pydantic import ValidationError

from app.server.knowledge import KnowledgeDocument


class TestKnowledgeDocument:
    def test_the_vrn_puts_the_owner_where_roles_grant_by_principal_id(self):
        document = KnowledgeDocument(id = "d1", owner_id = "o1", title = "guide.md", size_bytes = 1, chunk_count = 1)
        assert document.vrn == "vrn:knowledge:o1:document/d1"

    def test_a_negative_size_is_refused(self):
        with pytest.raises(ValidationError):
            KnowledgeDocument(owner_id = "o1", title = "x", size_bytes = -1, chunk_count = 0)
