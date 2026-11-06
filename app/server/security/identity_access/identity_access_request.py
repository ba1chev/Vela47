from pydantic import BaseModel, Field


class IdentityAccessRequest(BaseModel):
    """One question put to a policy: may these principals perform this action on this
    resource? Every kind of policy is evaluated against the same shape, which is what
    lets the authorization service union the verdicts of permission and resource
    policies without knowing which kind produced each one.

    principals is a list because a caller is more than one thing at once — an entity
    acting through a role — and a resource policy may name either of them. variables
    resolves the ${...} placeholders a statement may contain."""

    model_config = {"frozen": True}

    principals: list[str] = Field(
        description = "VRNs of every identity the caller presents — its entity, and its role "
            "once it holds one. A statement's principal patterns match when any of them does."
    )
    action: str = Field(
        description = "The action being attempted, as a 'service:Operation' string such as "
            "'agent:Run'. Matched case-insensitively against statement action patterns."
    )
    resource: str = Field(
        description = "VRN of the resource the action targets, e.g. 'vrn:agent::deep-agent'. "
            "Matched case-sensitively against statement resource patterns."
    )
    variables: dict[str, str] = Field(
        default_factory = dict,
        description = "Values for the ${...} placeholders statements may use — principal.id, "
            "principal.type and principal.role. A placeholder missing from this map makes the "
            "pattern containing it match nothing, never everything."
    )
