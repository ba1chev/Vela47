from typing import Any
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from db import TableBase
from db import JSON_DOCUMENT


class IdentityAccessResourcePolicyTable(TableBase):
    """One row per resource that has a resource-based policy attached, holding the policy
    as a JSON document. The document is stored whole rather than spread over columns
    because a policy is read and replaced as a unit and never queried by what it
    contains — a column per field would buy nothing but a migration every time the
    policy grammar grows."""

    __tablename__ = "identity_access_resource_policies"

    resource: Mapped[str] = mapped_column(
        String(512),
        primary_key = True,
        comment = "VRN of the resource the policy is attached to."
    )
    document: Mapped[dict[str, Any]] = mapped_column(
        JSON_DOCUMENT,
        comment = "The policy as IdentityAccessResourcePolicy.model_dump(mode='json') produces it."
    )
