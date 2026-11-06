from enum import Enum


class IdentityAccessAction(str, Enum):
    """The catalog of actions a request can attempt, written the way AWS writes them —
    `service:Operation`. Code that asks for authorization names its action from here, so
    a typo is an AttributeError at import time rather than a statement that silently
    never matches.

    Policies do not use this enum. Their action fields hold patterns — `agent:*`, `*` —
    which are not members of any catalog, and are matched against these values as plain
    strings. Adding a feature therefore means adding its actions here and granting them
    in a role; nothing in the evaluation engine changes."""

    AGENT_RUN = "agent:Run"
    IAM_ASSUME_ROLE = "iam:AssumeRole"
    IAM_CREATE_ENTITY = "iam:CreateEntity"
