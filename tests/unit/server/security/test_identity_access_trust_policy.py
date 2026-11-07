import pytest
from pydantic import ValidationError

from app.server.security import IdentityAccessRequest
from app.server.security import IdentityAccessPolicyType
from app.server.security import IdentityAccessTrustPolicy
from app.server.security import IdentityAccessPolicyEffect
from app.server.security import IdentityAccessPolicyStatement


def make_request(entity_vrn):
    return IdentityAccessRequest(
        principals = [entity_vrn], action = "iam:AssumeRole", resource = "vrn:iam::role/admin"
    )


def make_policy(principals = None, actions = None, resources = None):
    return IdentityAccessTrustPolicy(
        name = "Trust",
        statements = [
            IdentityAccessPolicyStatement(
                effect = IdentityAccessPolicyEffect.ALLOW,
                principals = ["vrn:iam::entity/admin/*"] if principals is None else principals,
                actions = ["iam:AssumeRole"] if actions is None else actions,
                resources = resources or []
            )
        ]
    )


class TestIdentityAccessTrustPolicy:
    def test_it_lets_a_trusted_entity_assume_the_role(self):
        verdict = make_policy().evaluate(make_request("vrn:iam::entity/admin/1"))
        assert verdict is IdentityAccessPolicyEffect.ALLOW

    def test_it_says_nothing_about_an_entity_it_does_not_trust(self):
        assert make_policy().evaluate(make_request("vrn:iam::entity/user/1")) is None

    def test_it_can_trust_one_specific_entity(self):
        policy = make_policy(principals = ["vrn:iam::entity/user/7"])
        assert policy.evaluate(make_request("vrn:iam::entity/user/7")) is IdentityAccessPolicyEffect.ALLOW
        assert policy.evaluate(make_request("vrn:iam::entity/user/8")) is None

    def test_resources_are_refused(self):
        with pytest.raises(ValidationError):
            make_policy(resources = ["vrn:iam::role/admin"])

    def test_an_action_other_than_assume_role_is_refused(self):
        with pytest.raises(ValidationError):
            make_policy(actions = ["iam:AssumeRole", "agent:Run"])

    def test_wildcards_that_cover_assume_role_are_accepted(self):
        assert make_policy(actions = ["iam:*"]).statements[0].actions == ["iam:*"]
        assert make_policy(actions = ["*"]).statements[0].actions == ["*"]

    def test_principals_are_required(self):
        with pytest.raises(ValidationError):
            make_policy(principals = [])

    def test_the_type_is_locked_to_trust(self):
        assert make_policy().type is IdentityAccessPolicyType.TRUST
