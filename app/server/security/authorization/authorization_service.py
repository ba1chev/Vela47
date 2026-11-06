from app.server.security.security_context import SecurityContext
from app.server.security.security_service_base import SecurityServiceBase
from app.server.security.security_service_type import SecurityServiceType
from app.server.security.authorization.authorization_error import AuthorizationError
from app.server.security.authorization.authorization_decision import AuthorizationDecision
from app.server.security.identity_access.identity_access_action import IdentityAccessAction
from app.server.security.identity_access.identity_access_request import IdentityAccessRequest
from app.server.security.identity_access.identity_access_service import IdentityAccessService
from app.server.security.identity_access.identity_access_role_session import IdentityAccessRoleSession
from app.server.security.identity_access.identity_access_policies.identity_access_policy_base import IdentityAccessPolicyBase
from app.server.security.identity_access.identity_access_policies.identity_access_policy_effect import IdentityAccessPolicyEffect


class AuthorizationService(SecurityServiceBase):
    """Decides whether an authenticated session may perform an action on a resource —
    the second stage of the pipeline, and an implementation of AWS's evaluation logic
    for requests within a single account.

    Every policy that could apply is gathered: the permission policies of the role the
    session acts through, and the resource policy attached to the target, if there is
    one. Each gives its own verdict and they combine in a fixed order — an explicit deny
    anywhere wins outright; failing that, an allow anywhere permits; failing that, the
    request is implicitly denied. A resource policy can therefore open a resource to a
    caller whose role grants nothing on it, which is what resource policies are for, but
    no allow in any document can override a deny.

    The role is looked up by name at evaluation time rather than read out of the token,
    so changing what a role may do takes effect on sessions that were already issued."""

    def __init__(self, identity_access_service: IdentityAccessService) -> None:
        self._identity_access_service: IdentityAccessService = identity_access_service

    @property
    def security_type(self) -> SecurityServiceType:
        return SecurityServiceType.AUTHORIZATION

    def evaluate(self, session: IdentityAccessRoleSession, action: IdentityAccessAction,
        resource: str) -> AuthorizationDecision:
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

        effects = [current_policy.evaluate(request) for current_policy in policies]
        if IdentityAccessPolicyEffect.DENY in effects:
            return AuthorizationDecision.EXPLICIT_DENY
        if IdentityAccessPolicyEffect.ALLOW in effects:
            return AuthorizationDecision.ALLOW
        return AuthorizationDecision.IMPLICIT_DENY

    def execute(self, context: SecurityContext) -> None:
        if context.session is None:
            raise RuntimeError(
                "Authorization ran without an authenticated session. Place the "
                "authentication service before it in the pipeline."
            )

        context.decision = self.evaluate(context.session, context.action, context.resource)

        if context.decision is AuthorizationDecision.EXPLICIT_DENY:
            raise AuthorizationError(
                f"'{context.action.value}' on '{context.resource}' is explicitly denied."
            )
        if context.decision is AuthorizationDecision.IMPLICIT_DENY:
            raise AuthorizationError(
                f"The {context.session.role_type.value} role is not allowed "
                f"'{context.action.value}' on '{context.resource}'."
            )
