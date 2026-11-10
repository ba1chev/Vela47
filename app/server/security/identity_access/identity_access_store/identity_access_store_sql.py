from typing import Optional
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from db import DatabaseBase
from db import IdentityEntityTable
from db import IdentityAccessResourcePolicyTable
from app.server.security import IdentityEntityBase
from app.server.security import IdentityEntityType
from app.server.security import IdentityEntityFactory
from app.server.security import IdentityAccessStoreBase
from app.server.security import IdentityEntityFactoryBase
from app.server.security import IdentityAccessResourcePolicy


class IdentityAccessStoreSql(IdentityAccessStoreBase):
    """Keeps identities and resource policies in the database, over SQLite in DEV and
    RDS in PROD alike, since it only talks to DatabaseBase; IdentityAccessStoreInMemory
    remains for tests. Rows become entities through IdentityEntityFactory and policies
    through their own model's validation, so a row that no longer fits fails loudly when
    read.

    add_entity() leaves name uniqueness to the table's unique constraint and turns
    the violation into ValueError, which makes it atomic across processes, not only
    threads."""

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
