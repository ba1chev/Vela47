import pytest
from pydantic import ValidationError

from app.server.security import IdentityAccessPolicyEffect
from app.server.security import IdentityAccessPolicyStatement


def make_statement(**overrides):
    fields = {
        "effect": IdentityAccessPolicyEffect.ALLOW,
        "actions": ["agent:Run"],
        "resources": ["vrn:agent::*"]
    }
    fields.update(overrides)
    return IdentityAccessPolicyStatement(**fields)


class TestIdentityAccessPolicyStatement:
    def test_at_least_one_action_is_required(self):
        with pytest.raises(ValidationError):
            make_statement(actions = [])

    def test_star_and_service_wildcards_are_valid_actions(self):
        assert make_statement(actions = ["*", "iam:*", "agent:Ru?"]).actions == ["*", "iam:*", "agent:Ru?"]

    def test_an_action_without_a_service_is_refused(self):
        with pytest.raises(ValidationError):
            make_statement(actions = ["Run"])

    def test_an_action_with_a_trailing_newline_is_refused(self):
        with pytest.raises(ValidationError):
            make_statement(actions = ["agent:Run\n"])

    def test_a_resource_that_is_not_a_vrn_is_refused(self):
        with pytest.raises(ValidationError):
            make_statement(resources = ["agent::deep-agent"])

    def test_a_principal_that_is_not_a_vrn_is_refused(self):
        with pytest.raises(ValidationError):
            make_statement(principals = ["admin"])

    def test_actions_match_case_insensitively(self):
        assert make_statement().matches_action("AGENT:RUN")

    def test_resources_match_case_sensitively(self):
        assert not make_statement(resources = ["vrn:agent::A"]).matches_resource("vrn:agent::a", {})

    def test_resources_resolve_variables(self):
        statement = make_statement(resources = ["vrn:session:${principal.id}:*"])
        assert statement.matches_resource("vrn:session:7:session/1", {"principal.id": "7"})
        assert not statement.matches_resource("vrn:session:8:session/1", {"principal.id": "7"})

    def test_a_principal_matches_when_any_presented_identity_does(self):
        statement = make_statement(principals = ["vrn:iam::role/admin"])
        assert statement.matches_principal(["vrn:iam::entity/admin/1", "vrn:iam::role/admin"])

    def test_no_principal_matches_when_none_is_presented(self):
        assert not make_statement(principals = ["*"]).matches_principal([])

    def test_statements_are_frozen(self):
        with pytest.raises(ValidationError):
            make_statement().effect = IdentityAccessPolicyEffect.DENY
