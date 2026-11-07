from db import TableBase
from db import ChatSessionTable
from db import IdentityEntityTable
from db import KnowledgeChunkTable
from db import KnowledgeDocumentTable
from db import IdentityAccessResourcePolicyTable


TABLE_REGISTRY: dict[str, type[TableBase]] = {
    IdentityEntityTable.__tablename__: IdentityEntityTable,
    IdentityAccessResourcePolicyTable.__tablename__: IdentityAccessResourcePolicyTable,
    ChatSessionTable.__tablename__: ChatSessionTable,
    KnowledgeDocumentTable.__tablename__: KnowledgeDocumentTable,
    KnowledgeChunkTable.__tablename__: KnowledgeChunkTable
}
