from app.server.security import IdentityEntityType
from app.server.security import IdentityAccessRoleType

VRN_PREFIX = "vrn"


def format_entity_vrn(entity_type: IdentityEntityType, entity_id: str) -> str:
    return f"{format_entity_type_vrn(entity_type)}/{entity_id}"


def format_entity_type_vrn(entity_type: IdentityEntityType) -> str:
    return f"{VRN_PREFIX}:iam::entity/{entity_type.value}"


def format_role_vrn(role_type: IdentityAccessRoleType) -> str:
    return f"{VRN_PREFIX}:iam::role/{role_type.value}"


def format_chat_session_vrn(owner_id: str, session_id: str) -> str:
    return f"{format_chat_session_collection_vrn(owner_id)}/{session_id}"


def format_chat_session_collection_vrn(owner_id: str) -> str:
    return f"{VRN_PREFIX}:session:{owner_id}:session"


def format_knowledge_document_vrn(owner_id: str, document_id: str) -> str:
    return f"{format_knowledge_collection_vrn(owner_id)}/{document_id}"


def format_knowledge_collection_vrn(owner_id: str) -> str:
    return f"{VRN_PREFIX}:knowledge:{owner_id}:document"
