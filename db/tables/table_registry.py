from db.tables.table_base import TableBase
from db.tables.chat_session_table import ChatSessionTable
from db.tables.identity_entity_table import IdentityEntityTable
from db.tables.identity_access_resource_policy_table import IdentityAccessResourcePolicyTable


TABLE_REGISTRY: dict[str, type[TableBase]] = {
    IdentityEntityTable.__tablename__: IdentityEntityTable,
    IdentityAccessResourcePolicyTable.__tablename__: IdentityAccessResourcePolicyTable,
    ChatSessionTable.__tablename__: ChatSessionTable
}
