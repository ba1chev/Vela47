from typing import Optional
from datetime import datetime, timedelta, timezone

from app.server.security.authorization.authorization_error import AuthorizationError
from app.server.security.identity_access.identity_access_action import IdentityAccessAction
from app.server.security.identity_access.identity_access_request import IdentityAccessRequest
from app.server.security.identity_access.identity_access_role_session import IdentityAccessRoleSession
from app.server.security.identity_access.identity_entities.identity_entity_base import IdentityEntityBase
from app.server.security.identity_access.identity_entities.identity_entity_type import IdentityEntityType
from app.server.security.authentication.authentication_password_hasher import AuthenticationPasswordHasher
from app.server.security.identity_access.identity_access_roles.identity_access_role_base import IdentityAccessRoleBase
from app.server.security.identity_access.identity_access_roles.identity_access_role_type import IdentityAccessRoleType
from app.server.security.identity_access.identity_access_store.identity_access_store_base import IdentityAccessStoreBase
from app.server.security.identity_access.identity_access_roles.identity_access_role_registry import IDENTITY_ACCESS_ROLE_REGISTRY
from app.server.security.identity_access.identity_access_policies.identity_access_policy_effect import IdentityAccessPolicyEffect
from app.server.security.identity_access.identity_entities.identity_entity_factory.identity_entity_factory import IdentityEntityFactory
from app.server.security.identity_access.identity_entities.identity_entity_factory.identity_entity_factory_base import IdentityEntityFactoryBase
from app.server.security.identity_access.identity_access_policies.identity_access_resource_policy.identity_access_resource_policy import IdentityAccessResourcePolicy


class IdentityAccessService:
    """The identity and access directory — the counterpart of the IAM control plane
    together with STS's AssumeRole. It owns every rule about identity: which kinds may be
    created and under what names, which role an entity may act through, how long a role
    session lasts, and which resource policies are attached where. Authentication and
    authorization both consult it, and neither keeps any identity state of its own.

    Storage is delegated to a store, so the same service runs over memory today and over
    the database once it exists. Roles are not stored: the built-in ones are code, built
    once from the registry when the service is constructed.

    assume_role() is the one gate between proving who you are and being allowed to do
    anything at all. It evaluates the target role's trust policy against the entity and
    refuses unless that policy explicitly allows it — a role whose trust policy says
    nothing about an entity is a role that entity cannot have."""

    def __init__(self, store: IdentityAccessStoreBase,
        password_hasher: AuthenticationPasswordHasher) -> None:
        self._store: IdentityAccessStoreBase = store
        self._password_hasher: AuthenticationPasswordHasher = password_hasher
        self._entity_factory: IdentityEntityFactoryBase = IdentityEntityFactory()
        self._roles: dict[IdentityAccessRoleType, IdentityAccessRoleBase] = {
            current_type: current_class()
            for current_type, current_class in IDENTITY_ACCESS_ROLE_REGISTRY.items()
        }

    def create_entity(self, entity_type: IdentityEntityType, name: str,
        password: str) -> IdentityEntityBase:
        if entity_type is IdentityEntityType.GUEST:
            raise ValueError(
                "Guests are issued on demand and never registered — use create_guest()."
            )

        entity = self._entity_factory.create(
            entity_type,
            name = name,
            password_hash = self._password_hasher.hash(password)
        )
        self._store.add_entity(entity)
        return entity

    def create_guest(self) -> IdentityEntityBase:
        return self._entity_factory.create(IdentityEntityType.GUEST)

    def get_entity(self, entity_id: str) -> Optional[IdentityEntityBase]:
        return self._store.get_entity(entity_id)

    def find_entity(self, name: str) -> Optional[IdentityEntityBase]:
        return self._store.find_entity(name.strip().lower())

    def resolve_entity(self, session: IdentityAccessRoleSession) -> Optional[IdentityEntityBase]:
        if session.entity_type is IdentityEntityType.GUEST:
            return self._entity_factory.create(IdentityEntityType.GUEST, id = session.entity_id)

        entity = self._store.get_entity(session.entity_id)
        if entity is None or entity.type is not session.entity_type:
            return None
        return entity

    def get_role(self, role_type: IdentityAccessRoleType) -> IdentityAccessRoleBase:
        role = self._roles.get(role_type)

        if role is None:
            raise ValueError(
                f"No role registered for type '{role_type}'. "
                f"Known types: {list(self._roles)}"
            )

        return role

    def assume_role(self, entity: IdentityEntityBase,
        role_type: Optional[IdentityAccessRoleType] = None) -> IdentityAccessRoleSession:
        role = self.get_role(role_type if role_type is not None else entity.default_role)
        verdict = role.trust_policy.evaluate(IdentityAccessRequest(
            principals = [entity.vrn],
            action = IdentityAccessAction.IAM_ASSUME_ROLE.value,
            resource = role.vrn
        ))

        if verdict is not IdentityAccessPolicyEffect.ALLOW:
            raise AuthorizationError(
                f"The {role.role_type.value} role does not trust this identity."
            )

        issued_at = datetime.now(timezone.utc).replace(microsecond = 0)
        return IdentityAccessRoleSession(
            entity_id = entity.id,
            entity_type = entity.type,
            role_type = role.role_type,
            issued_at = issued_at,
            expires_at = issued_at + timedelta(seconds = role.max_session_seconds)
        )

    def put_resource_policy(self, resource: str, policy: IdentityAccessResourcePolicy) -> None:
        self._store.put_resource_policy(resource, policy)

    def get_resource_policy(self, resource: str) -> Optional[IdentityAccessResourcePolicy]:
        return self._store.get_resource_policy(resource)
