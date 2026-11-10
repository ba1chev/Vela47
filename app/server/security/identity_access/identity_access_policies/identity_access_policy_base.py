from typing import Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field

from app.server.security import IdentityAccessRequest
from app.server.security import IdentityAccessPolicyType
from app.server.security import IdentityAccessPolicyEffect
from app.server.security import IdentityAccessPolicyStatement


class IdentityAccessPolicyBase(BaseModel, ABC):
    """Abstract base for every policy document: a name, a list of statements and the
    rule by which they reach a verdict. Policies are data, so they can be built, stored
    and replaced at runtime without the evaluation engine noticing.

    evaluate() answers DENY if a covering statement denies, ALLOW if one allows and none
    denies, and None if none covers the request. None is no opinion, not a denial; the
    authorization service turns the absence of any ALLOW into the implicit deny. Which
    statements cover a request is the one thing the kinds disagree on, so it is left
    abstract."""

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
