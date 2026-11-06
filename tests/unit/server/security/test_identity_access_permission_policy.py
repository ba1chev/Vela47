import pytest
from pydantic import ValidationError

from app.server.security.identity_access.identity_access_request import IdentityAccessRequest
from app.server.security.identity_access.identity_access_policies.identity_access_policy_base import IdentityAccessPolicyBase
from app.server.security.identity_access.identity_access_policies.identity_access_policy_type import IdentityAccessPolicyType
from app.server.security.identity_access.identity_access_policies.identity_access_policy_effect import IdentityAccessPolicyEffect
from app.server.security.identity_access.identity_access_policies.identity_access_policy_statement import IdentityAccessPolicyStatement
from app.server.security.identity_access.identity_access_policies.identity_access_permission_policy.identity_access_permission_policy import IdentityAccessPermissionPolicy


def make_request(action = "agent:Run", resource = "vrn:agent::deep-agent", variables = None):
    return IdentityAccessRequest(
        principals = ["vrn:iam::entity/user/1", "vrn:iam::role/user"],
        action = action,
        resource = resource,
        variables = variables or {}
    )


def make_statement(effect, actions, resources, **extra):
    return IdentityAccessPolicyStatement(
        effect = effect, actions = actions, resources = resources, **extra
    )


def make_policy(*statements):
    return IdentityAccessPermissionPolicy(name = "Test", statements = list(statements))


ALLOW = IdentityAccessPolicyEffect.ALLOW
DENY = IdentityAccessPolicyEffect.DENY


class TestIdentityAccessPermissionPolicy:
    def test_a_covering_allow_allows(self):
        policy = make_policy(make_statement(ALLOW, ["agent:Run"], ["vrn:agent::*"]))
        assert policy.evaluate(make_request()) is ALLOW

    def test_a_request_no_statement_covers_gets_no_verdict(self):
        policy = make_policy(make_statement(ALLOW, ["agent:Run"], ["vrn:agent::*"]))
        assert policy.evaluate(make_request(action = "iam:CreateEntity")) is None

    def test_deny_wins_over_allow_whatever_their_order(self):
        allow = make_statement(ALLOW, ["*"], ["*"])
        deny = make_statement(DENY, ["agent:Run"], ["*"])
        assert make_policy(allow, deny).evaluate(make_request()) is DENY
        assert make_policy(deny, allow).evaluate(make_request()) is DENY

    def test_a_deny_that_does_not_cover_the_request_changes_nothing(self):
        allow = make_statement(ALLOW, ["*"], ["*"])
        deny = make_statement(DENY, ["iam:*"], ["*"])
        assert make_policy(allow, deny).evaluate(make_request()) is ALLOW

    def test_principals_are_refused(self):
        with pytest.raises(ValidationError):
            make_policy(make_statement(ALLOW, ["*"], ["*"], principals = ["*"]))

    def test_a_statement_without_resources_is_refused(self):
        with pytest.raises(ValidationError):
            make_policy(make_statement(ALLOW, ["*"], []))

    def test_a_policy_needs_at_least_one_statement(self):
        with pytest.raises(ValidationError):
            make_policy()

    def test_the_type_is_locked_to_permission(self):
        policy = make_policy(make_statement(ALLOW, ["*"], ["*"]))
        assert policy.type is IdentityAccessPolicyType.PERMISSION

    def test_own_resources_are_granted_through_the_principal_id_variable(self):
        policy = make_policy(make_statement(ALLOW, ["agent:Run"], ["vrn:session:${principal.id}:*"]))
        own = make_request(resource = "vrn:session:1:session/a", variables = {"principal.id": "1"})
        other = make_request(resource = "vrn:session:2:session/a", variables = {"principal.id": "1"})
        assert policy.evaluate(own) is ALLOW
        assert policy.evaluate(other) is None

    def test_the_base_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            IdentityAccessPolicyBase(
                type = IdentityAccessPolicyType.PERMISSION,
                name = "x",
                statements = [make_statement(ALLOW, ["*"], ["*"])]
            )
