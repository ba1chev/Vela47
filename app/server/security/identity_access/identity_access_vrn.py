from app.server.security import IdentityEntityType
from app.server.security import IdentityAccessRoleType

VRN_PREFIX = "vrn"


def format_entity_vrn(entity_type: IdentityEntityType, entity_id: str) -> str:
    return f"{format_entity_type_vrn(entity_type)}/{entity_id}"


def format_entity_type_vrn(entity_type: IdentityEntityType) -> str:
    return f"{VRN_PREFIX}:iam::entity/{entity_type.value}"


def format_role_vrn(role_type: IdentityAccessRoleType) -> str:
    return f"{VRN_PREFIX}:iam::role/{role_type.value}"
