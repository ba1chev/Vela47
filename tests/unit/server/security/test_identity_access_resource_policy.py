import pytest
from pydantic import ValidationError

from app.server.security.identity_access.identity_access_request import IdentityAccessRequest
from app.server.security.identity_access.identity_access_policies.identity_access_policy_type import IdentityAccessPolicyType
from app.server.security.identity_access.identity_access_policies.identity_access_policy_effect import IdentityAccessPolicyEffect
from app.server.security.identity_access.identity_access_policies.identity_access_policy_statement import IdentityAccessPolicyStatement
from app.server.security.identity_access.identity_access_policies.identity_access_resource_policy.identity_access_resource_policy import IdentityAccessResourcePolicy
from app.server.security.identity_access.identity_access_policies.identity_access_resource_policy.identity_access_resource_policy_base import IdentityAccessResourcePolicyBase

RESOURCE = "vrn:session:1:session/a"


def make_request(principals):
    return IdentityAccessRequest(principals = principals, action = "agent:Run", resource = RESOURCE)


def make_policy(principals, resources = None):
    return IdentityAccessResourcePolicy(
        name = "Share",
        statements = [
            IdentityAccessPolicyStatement(
                effect = IdentityAccessPolicyEffect.ALLOW,
                principals = principals,
                actions = ["agent:Run"],
                resources = [RESOURCE] if resources is None else resources
            )
        ]
    )


class TestIdentityAccessResourcePolicy:
    def test_principals_are_required(self):
        with pytest.raises(ValidationError):
            make_policy([])

    def test_resources_are_required(self):
        with pytest.raises(ValidationError):
            make_policy(["*"], resources = [])

    def test_it_grants_to_a_named_entity_whatever_role_it_holds(self):
        policy = make_policy(["vrn:iam::entity/user/2"])
        verdict = policy.evaluate(make_request(["vrn:iam::entity/user/2", "vrn:iam::role/guest"]))
        assert verdict is IdentityAccessPolicyEffect.ALLOW

    def test_it_grants_to_everyone_acting_as_a_role(self):
        policy = make_policy(["vrn:iam::role/admin"])
        verdict = policy.evaluate(make_request(["vrn:iam::entity/admin/9", "vrn:iam::role/admin"]))
        assert verdict is IdentityAccessPolicyEffect.ALLOW

    def test_it_says_nothing_about_a_principal_it_does_not_name(self):
        policy = make_policy(["vrn:iam::entity/user/2"])
        assert policy.evaluate(make_request(["vrn:iam::entity/user/3", "vrn:iam::role/user"])) is None

    def test_the_type_is_locked_to_resource(self):
        assert make_policy(["*"]).type is IdentityAccessPolicyType.RESOURCE

    def test_the_base_is_abstract(self):
        with pytest.raises(TypeError):
            IdentityAccessResourcePolicyBase(
                type = IdentityAccessPolicyType.RESOURCE,
                name = "x",
                statements = make_policy(["*"]).statements
            )
