from typing import Optional

from app.server.security import SecurityContext
from app.server.security import AuthorizationError
from app.server.security import SecurityServiceBase
from app.server.security import SecurityServiceType
from app.server.security import IdentityAccessAction
from app.server.security import AuthorizationDecision
from app.server.security import IdentityAccessRequest
from app.server.security import IdentityAccessService
from app.server.security import IdentityAccessPolicyBase
from app.server.security import IdentityAccessRoleSession
from app.server.security import IdentityAccessPolicyEffect
from app.intelligence.tracing import current_tracing_service


class AuthorizationService(SecurityServiceBase):
    """Decides whether a session may perform an action on a resource: the second stage
    of the pipeline, following AWS's evaluation logic within one account. The permission
    policies of the session's role and the resource policy of the target each give a
    verdict; an explicit deny anywhere wins, then any allow, otherwise the request is
    implicitly denied. A resource policy can open a resource to a role that grants
    nothing on it, but no allow overrides a deny.

    The role is looked up at evaluation time rather than read from the token, so a
    changed role applies to sessions already issued."""

    def __init__(self, identity_access_service: IdentityAccessService) -> None:
        self._identity_access_service: IdentityAccessService = identity_access_service

    @property
    def security_type(self) -> SecurityServiceType:
        return SecurityServiceType.AUTHORIZATION

    def evaluate(self, session: IdentityAccessRoleSession, action: IdentityAccessAction,
        resource: str) -> AuthorizationDecision:
        return self._decide(self._effects(session, action, resource))

    def _decide(self, effects: list[tuple[IdentityAccessPolicyBase, Optional[IdentityAccessPolicyEffect]]]) -> AuthorizationDecision:
        verdicts = [current_effect for _, current_effect in effects]
        if IdentityAccessPolicyEffect.DENY in verdicts:
            return AuthorizationDecision.EXPLICIT_DENY
        if IdentityAccessPolicyEffect.ALLOW in verdicts:
            return AuthorizationDecision.ALLOW
        return AuthorizationDecision.IMPLICIT_DENY

    def _effects(self, session: IdentityAccessRoleSession, action: IdentityAccessAction,
        resource: str) -> list[tuple[IdentityAccessPolicyBase, Optional[IdentityAccessPolicyEffect]]]:
        role = self._identity_access_service.get_role(session.role_type)
        request = IdentityAccessRequest(
            principals = session.principals,
            action = action.value,
            resource = resource,
            variables = session.variables
        )

        policies: list[IdentityAccessPolicyBase] = list(role.permission_policies)
        resource_policy = self._identity_access_service.get_resource_policy(resource)
        if resource_policy is not None:
            policies.append(resource_policy)

        return [(current_policy, current_policy.evaluate(request)) for current_policy in policies]

    def execute(self, context: SecurityContext) -> None:
        if context.session is None:
            raise RuntimeError(
                "Authorization ran without an authenticated session. Place the "
                "authentication service before it in the pipeline."
            )

        effects = self._effects(context.session, context.action, context.resource)
        context.decision = self._decide(effects)
        current_tracing_service().record(f"{context.action.value} · {context.decision.value}", "auth", {
            "detail": f"{context.session.role_type.value} on {context.resource}",
            "action": context.action.value,
            "resource": context.resource,
            "role": context.session.role_type.value,
            "entity_type": context.session.entity_type.value,
            "decision": context.decision.value,
            "policies": [
                {"name": current_policy.name, "type": current_policy.type.value, "effect": current_effect.value if current_effect else None}
                for current_policy, current_effect in effects
            ],
            **({"status": "error", "error": f"{context.decision.value}"} if context.decision is not AuthorizationDecision.ALLOW else {})
        })

        if context.decision is AuthorizationDecision.EXPLICIT_DENY:
            raise AuthorizationError(
                f"'{context.action.value}' on '{context.resource}' is explicitly denied."
            )
        if context.decision is AuthorizationDecision.IMPLICIT_DENY:
            raise AuthorizationError(
                f"The {context.session.role_type.value} role is not allowed "
                f"'{context.action.value}' on '{context.resource}'."
            )
