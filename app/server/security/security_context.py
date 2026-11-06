from typing import Optional
from pydantic import BaseModel, Field

from app.server.security.authorization.authorization_decision import AuthorizationDecision
from app.server.security.identity_access.identity_access_action import IdentityAccessAction
from app.server.security.identity_access.identity_access_role_session import IdentityAccessRoleSession


class SecurityContext(BaseModel):
    """The single mutable object threaded through every service of a SecurityPipeline,
    the way OperationContext is threaded through the operation layers. The caller fills
    in what the request wants — the token it presented, the action it attempts and the
    resource it targets — and each service writes the one field it owns: authentication
    writes session, authorization writes decision.

    Nothing here is trusted until a service has vouched for it. The token is whatever the
    client sent; a session exists only once authentication has verified one; and the
    request is allowed only once a decision of ALLOW has been written. Unlike the policy
    models this is intentionally not frozen — writing into it is how services report."""

    token: Optional[str] = Field(
        default = None,
        repr = False,
        exclude = True,
        description = "The raw session token the client presented, or None when it presented "
            "none. Kept out of repr and dumps, so logging a context never leaks a credential."
    )
    action: IdentityAccessAction = Field(
        description = "What the request attempts to do, named from the action catalog. Every "
            "applicable statement's action patterns are matched against its value."
    )
    resource: str = Field(
        description = "VRN of the thing the action targets, e.g. 'vrn:agent::deep-agent'. "
            "Matched against statement resource patterns, and used to find the resource "
            "policy attached to it."
    )
    session: Optional[IdentityAccessRoleSession] = Field(
        default = None,
        description = "The caller's verified role session. None until authentication has run, "
            "which is also how authorization notices it was placed in a pipeline without "
            "authentication in front of it."
    )
    decision: Optional[AuthorizationDecision] = Field(
        default = None,
        description = "The outcome of policy evaluation. None until authorization has run; the "
            "pipeline treats anything other than ALLOW — None included — as a denial."
    )

    @property
    def allowed(self) -> bool:
        return self.decision is AuthorizationDecision.ALLOW
