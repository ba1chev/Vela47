from typing import Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field

from app.server.security.identity_access.identity_access_request import IdentityAccessRequest
from app.server.security.identity_access.identity_access_policies.identity_access_policy_type import IdentityAccessPolicyType
from app.server.security.identity_access.identity_access_policies.identity_access_policy_effect import IdentityAccessPolicyEffect
from app.server.security.identity_access.identity_access_policies.identity_access_policy_statement import IdentityAccessPolicyStatement


class IdentityAccessPolicyBase(BaseModel, ABC):
    """Abstract base for every policy document: the grammar all three kinds share — a
    name and a list of statements — and the one rule by which each reaches a verdict.
    Policies are data, not code. A document can be built, attached, stored and replaced
    at runtime, which is what lets policies move into the database later without the
    evaluation engine noticing.

    evaluate() gives this document's verdict on one request: DENY if any statement that
    covers the request denies it, ALLOW if one allows it and none denies, and None if no
    statement covers it at all. None is not a denial — it means this document has no
    opinion, and it is the authorization service that turns the absence of an ALLOW
    across every document into the implicit deny.

    Which statements cover a request is the one thing the kinds disagree on, so it is
    the one thing left abstract: a permission policy compares action and resource, a
    resource policy the principal as well, and a trust policy the principal and the
    action alone."""

    model_config = {"frozen": True}

    type: IdentityAccessPolicyType = Field(
        description = "Discriminator naming the kind of document. Each concrete subclass locks it "
            "to a Literal, so a stored document can be loaded back into the right class without "
            "isinstance checks."
    )
    name: str = Field(
        min_length = 1,
        description = "Human-readable name of the document, e.g. 'AdministratorAccess'. Shown in "
            "errors and listings; evaluation never reads it."
    )
    statements: list[IdentityAccessPolicyStatement] = Field(
        min_length = 1,
        description = "The rules this document consists of, evaluated together. Order does not "
            "matter — a DENY anywhere in the list wins wherever the ALLOW sits."
    )

    @abstractmethod
    def covers(self, statement: IdentityAccessPolicyStatement,
        request: IdentityAccessRequest) -> bool:
        raise NotImplementedError("Must be implemented")

    def evaluate(self, request: IdentityAccessRequest) -> Optional[IdentityAccessPolicyEffect]:
        effects = {
            current_statement.effect
            for current_statement in self.statements
            if self.covers(current_statement, request)
        }

        if IdentityAccessPolicyEffect.DENY in effects:
            return IdentityAccessPolicyEffect.DENY
        if IdentityAccessPolicyEffect.ALLOW in effects:
            return IdentityAccessPolicyEffect.ALLOW
        return None
