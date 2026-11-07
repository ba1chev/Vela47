import pytest

from app.server.security import SecurityContext
from app.server.security import AuthorizationError
from app.server.security import IdentityEntityType
from app.server.security import SecurityServiceType
from app.server.security import AuthorizationService
from app.server.security import IdentityAccessAction
from app.server.security import AuthorizationDecision
from app.server.security import IdentityAccessService
from app.server.security import IdentityAccessRoleType
from app.server.security import IdentityAccessPolicyEffect
from app.server.security import IdentityAccessStoreInMemory
from app.server.security import AuthenticationPasswordHasher
from app.server.security import IdentityAccessResourcePolicy
from app.server.security import IdentityAccessPolicyStatement

PASSWORD = "correct-horse-battery"
AGENT = "vrn:agent::deep-agent"
USERS = "vrn:iam::entity/user"


def make_service():
    hasher = AuthenticationPasswordHasher(cost = 16, block_size = 1)
    return IdentityAccessService(IdentityAccessStoreInMemory(), hasher)


def make_session(service, entity_type, name, role_type = None):
    return service.assume_role(service.create_entity(entity_type, name, PASSWORD), role_type)


def make_resource_policy(effect, principals, actions, resources):
    return IdentityAccessResourcePolicy(
        name = "Attached",
        statements = [
            IdentityAccessPolicyStatement(
                effect = effect, principals = principals, actions = actions, resources = resources
            )
        ]
    )


class TestAuthorizationService:
    def test_its_type_is_authorization(self):
        assert AuthorizationService(make_service()).security_type is SecurityServiceType.AUTHORIZATION

    def test_admin_is_allowed_anything(self):
        service = make_service()
        session = make_session(service, IdentityEntityType.ADMIN, "root")
        decision = AuthorizationService(service).evaluate(session, IdentityAccessAction.IAM_CREATE_ENTITY, USERS)
        assert decision is AuthorizationDecision.ALLOW

    def test_user_may_run_the_agent(self):
        service = make_service()
        session = make_session(service, IdentityEntityType.USER, "ana")
        decision = AuthorizationService(service).evaluate(session, IdentityAccessAction.AGENT_RUN, AGENT)
        assert decision is AuthorizationDecision.ALLOW

    def test_guest_may_run_the_agent(self):
        service = make_service()
        session = service.assume_role(service.create_guest())
        decision = AuthorizationService(service).evaluate(session, IdentityAccessAction.AGENT_RUN, AGENT)
        assert decision is AuthorizationDecision.ALLOW

    def test_user_creating_entities_is_an_implicit_deny(self):
        service = make_service()
        session = make_session(service, IdentityEntityType.USER, "ana")
        decision = AuthorizationService(service).evaluate(session, IdentityAccessAction.IAM_CREATE_ENTITY, USERS)
        assert decision is AuthorizationDecision.IMPLICIT_DENY

    def test_guest_creating_entities_is_an_explicit_deny(self):
        service = make_service()
        session = service.assume_role(service.create_guest())
        decision = AuthorizationService(service).evaluate(session, IdentityAccessAction.IAM_CREATE_ENTITY, USERS)
        assert decision is AuthorizationDecision.EXPLICIT_DENY

    def test_an_admin_working_as_the_user_role_has_only_user_rights(self):
        service = make_service()
        session = make_session(service, IdentityEntityType.ADMIN, "root", IdentityAccessRoleType.USER)
        decision = AuthorizationService(service).evaluate(session, IdentityAccessAction.IAM_CREATE_ENTITY, USERS)
        assert decision is AuthorizationDecision.IMPLICIT_DENY

    def test_a_resource_policy_can_open_a_resource_to_one_user(self):
        service = make_service()
        ana = make_session(service, IdentityEntityType.USER, "ana")
        bob = make_session(service, IdentityEntityType.USER, "bob")
        service.put_resource_policy(USERS, make_resource_policy(
            IdentityAccessPolicyEffect.ALLOW, [ana.entity_vrn], ["iam:CreateEntity"], [USERS]
        ))
        authorization_service = AuthorizationService(service)
        assert authorization_service.evaluate(ana, IdentityAccessAction.IAM_CREATE_ENTITY, USERS) is AuthorizationDecision.ALLOW
        assert authorization_service.evaluate(bob, IdentityAccessAction.IAM_CREATE_ENTITY, USERS) is AuthorizationDecision.IMPLICIT_DENY

    def test_a_resource_policy_can_grant_to_everyone_acting_as_a_role(self):
        service = make_service()
        ana = make_session(service, IdentityEntityType.USER, "ana")
        service.put_resource_policy(USERS, make_resource_policy(
            IdentityAccessPolicyEffect.ALLOW, ["vrn:iam::role/user"], ["iam:CreateEntity"], [USERS]
        ))
        decision = AuthorizationService(service).evaluate(ana, IdentityAccessAction.IAM_CREATE_ENTITY, USERS)
        assert decision is AuthorizationDecision.ALLOW

    def test_a_resource_policy_cannot_override_the_guests_explicit_deny(self):
        service = make_service()
        guest = service.assume_role(service.create_guest())
        service.put_resource_policy(USERS, make_resource_policy(
            IdentityAccessPolicyEffect.ALLOW, ["*"], ["iam:CreateEntity"], [USERS]
        ))
        decision = AuthorizationService(service).evaluate(guest, IdentityAccessAction.IAM_CREATE_ENTITY, USERS)
        assert decision is AuthorizationDecision.EXPLICIT_DENY

    def test_a_resource_deny_overrides_even_the_admin_allow(self):
        service = make_service()
        admin = make_session(service, IdentityEntityType.ADMIN, "root")
        service.put_resource_policy(AGENT, make_resource_policy(
            IdentityAccessPolicyEffect.DENY, ["vrn:iam::role/admin"], ["agent:Run"], [AGENT]
        ))
        decision = AuthorizationService(service).evaluate(admin, IdentityAccessAction.AGENT_RUN, AGENT)
        assert decision is AuthorizationDecision.EXPLICIT_DENY

    def test_execute_records_the_decision_even_when_it_refuses(self):
        service = make_service()
        context = SecurityContext(
            action = IdentityAccessAction.IAM_CREATE_ENTITY,
            resource = USERS,
            session = make_session(service, IdentityEntityType.USER, "ana")
        )
        with pytest.raises(AuthorizationError):
            AuthorizationService(service).execute(context)
        assert context.decision is AuthorizationDecision.IMPLICIT_DENY

    def test_execute_allows_by_writing_allow(self):
        service = make_service()
        context = SecurityContext(
            action = IdentityAccessAction.AGENT_RUN,
            resource = AGENT,
            session = make_session(service, IdentityEntityType.USER, "ana")
        )
        AuthorizationService(service).execute(context)
        assert context.allowed

    def test_execute_without_a_session_is_a_configuration_error(self):
        context = SecurityContext(action = IdentityAccessAction.AGENT_RUN, resource = AGENT)
        with pytest.raises(RuntimeError):
            AuthorizationService(make_service()).execute(context)
