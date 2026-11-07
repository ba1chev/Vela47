import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.server.security import VRN_PREFIX
from app.server.security import matches_pattern
from app.server.security import IdentityAccessPolicyEffect

ACTION_PATTERN = re.compile(r"\*|[a-z0-9*?-]+:[A-Za-z0-9*?]+")


class IdentityAccessPolicyStatement(BaseModel):
    """One rule inside a policy document, in AWS's grammar: an effect, the actions it
    covers and the resources it covers — plus, in documents attached to something other
    than an identity, the principals it applies to. Every one of those fields holds
    patterns, not literals: `*` matches any run of characters, `?` exactly one, and
    `${...}` is replaced by a variable of the request being evaluated. That last one is
    what lets a single statement grant every caller only its own resources —
    vrn:session:${principal.id}:* — and a variable the request cannot resolve makes the
    pattern match nothing, never everything. A resolved value is matched literally, so
    an id that happened to contain `*` could not widen the grant.

    Resources and principals are VRNs, the counterpart of ARNs:
    vrn:<service>:<owner>:<resource>, e.g. vrn:iam::entity/user/9f2c… for an entity or
    vrn:agent::deep-agent for the agent. Malformed patterns are refused at construction,
    because a pattern that can never match fails in the safest-looking way possible — as
    a permission that quietly never applies.

    Which fields must be present depends on where the statement lives, so that is
    enforced by the policy kinds rather than here: a permission policy forbids
    principals, a resource policy requires them, and a trust policy forbids resources."""

    model_config = {"frozen": True}

    sid: Optional[str] = Field(
        default = None,
        description = "Statement id — a short label such as 'AdminEntitiesOnly', like AWS's Sid. "
            "Exists for the people reading and debugging a policy; it never affects evaluation."
    )
    effect: IdentityAccessPolicyEffect = Field(
        description = "Whether this statement grants or forbids what it covers. A DENY that "
            "applies wins over every ALLOW in every document evaluated for the same request."
    )
    actions: list[str] = Field(
        min_length = 1,
        description = "Action patterns this statement covers, each '*' or 'service:Operation' — "
            "e.g. 'agent:Run' or 'iam:*'. Matched case-insensitively, as AWS matches actions."
    )
    resources: list[str] = Field(
        default_factory = list,
        description = "VRN patterns of the resources this statement covers, or '*'. Required in "
            "permission and resource policies, forbidden in trust policies, whose resource is "
            "always the role itself. Matched case-sensitively."
    )
    principals: list[str] = Field(
        default_factory = list,
        description = "VRN patterns of the principals this statement applies to, or '*'. "
            "Required in resource and trust policies, forbidden in permission policies, whose "
            "principal is whoever holds the role they are attached to."
    )

    @field_validator("actions")
    @classmethod
    def validate_actions(cls, actions: list[str]) -> list[str]:
        for current_action in actions:
            if not ACTION_PATTERN.fullmatch(current_action):
                raise ValueError(
                    f"Action '{current_action}' is neither '*' nor of the form 'service:Operation'."
                )
        return actions

    @field_validator("resources", "principals")
    @classmethod
    def validate_names(cls, names: list[str]) -> list[str]:
        for current_name in names:
            if current_name != "*" and not current_name.startswith(f"{VRN_PREFIX}:"):
                raise ValueError(
                    f"'{current_name}' is neither '*' nor a VRN starting with '{VRN_PREFIX}:'."
                )
        return names

    def matches_action(self, action: str) -> bool:
        return any(
            matches_pattern(current_pattern, action, case_sensitive = False)
            for current_pattern in self.actions
        )

    def matches_resource(self, resource: str, variables: dict[str, str]) -> bool:
        return any(
            matches_pattern(current_pattern, resource, variables)
            for current_pattern in self.resources
        )

    def matches_principal(self, principals: list[str]) -> bool:
        return any(
            matches_pattern(current_pattern, current_principal)
            for current_pattern in self.principals
            for current_principal in principals
        )
