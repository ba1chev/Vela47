from typing import Optional
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from db.database_base import DatabaseBase
from db.tables.identity_entity_table import IdentityEntityTable
from db.tables.identity_access_resource_policy_table import IdentityAccessResourcePolicyTable
from app.server.security.identity_access.identity_entities.identity_entity_base import IdentityEntityBase
from app.server.security.identity_access.identity_entities.identity_entity_type import IdentityEntityType
from app.server.security.identity_access.identity_access_store.identity_access_store_base import IdentityAccessStoreBase
from app.server.security.identity_access.identity_entities.identity_entity_factory.identity_entity_factory import IdentityEntityFactory
from app.server.security.identity_access.identity_entities.identity_entity_factory.identity_entity_factory_base import IdentityEntityFactoryBase
from app.server.security.identity_access.identity_access_policies.identity_access_resource_policy.identity_access_resource_policy import IdentityAccessResourcePolicy


class IdentityAccessStoreSql(IdentityAccessStoreBase):
    """Keeps identities and resource policies in the database, so accounts outlive the
    process — the store the server runs on, with IdentityAccessStoreInMemory kept for
    tests that need no database at all. It works the same over the SQLite file in DEV
    and over RDS in PROD, because it only ever talks to DatabaseBase.

    Rows and models are translated here and nowhere else. A row becomes an entity
    through IdentityEntityFactory, keyed on the stored type, and a policy document goes
    back through its own model's validation, so a row that no longer matches its model
    fails loudly when read instead of being half-trusted.

    add_entity() leaves the uniqueness of names to the table's unique constraint and turns
    the violation into the ValueError the store contract promises. That is what makes it
    atomic across processes and not just threads: two EC2 instances creating the same
    name at once still end with exactly one account."""

    def __init__(self, database: DatabaseBase) -> None:
        self._database: DatabaseBase = database
        self._entity_factory: IdentityEntityFactoryBase = IdentityEntityFactory()

    def _to_entity(self, row: IdentityEntityTable) -> IdentityEntityBase:
        return self._entity_factory.create(
            IdentityEntityType(row.type),
            id = row.id,
            name = row.name,
            password_hash = row.password_hash,
            created_at = row.created_at
        )

    def add_entity(self, entity: IdentityEntityBase) -> None:
        if entity.password_hash is None:
            raise ValueError(
                f"Only entities with credentials are stored — a {entity.type.value} has none."
            )

        try:
            with self._database.transaction() as transaction:
                transaction.add(IdentityEntityTable(
                    id = entity.id,
                    type = entity.type.value,
                    name = entity.name,
                    password_hash = entity.password_hash.get_secret_value(),
                    created_at = entity.created_at
                ))
        except IntegrityError:
            raise ValueError(f"The name '{entity.name}' is already taken.") from None

    def get_entity(self, entity_id: str) -> Optional[IdentityEntityBase]:
        with self._database.transaction() as transaction:
            row = transaction.get(IdentityEntityTable, entity_id)
            return self._to_entity(row) if row is not None else None

    def find_entity(self, name: str) -> Optional[IdentityEntityBase]:
        with self._database.transaction() as transaction:
            row = transaction.scalars(
                select(IdentityEntityTable).where(IdentityEntityTable.name == name)
            ).one_or_none()
            return self._to_entity(row) if row is not None else None

    def put_resource_policy(self, resource: str, policy: IdentityAccessResourcePolicy) -> None:
        with self._database.transaction() as transaction:
            transaction.merge(IdentityAccessResourcePolicyTable(
                resource = resource,
                document = policy.model_dump(mode = "json")
            ))

    def get_resource_policy(self, resource: str) -> Optional[IdentityAccessResourcePolicy]:
        with self._database.transaction() as transaction:
            row = transaction.get(IdentityAccessResourcePolicyTable, resource)
            return IdentityAccessResourcePolicy.model_validate(row.document) if row is not None else None
