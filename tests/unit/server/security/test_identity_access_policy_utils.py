from app.server.security.identity_access.identity_access_policies.identity_access_policy_utils import matches_pattern


class TestMatchesPattern:
    def test_a_literal_matches_only_itself(self):
        assert matches_pattern("agent:Run", "agent:Run")
        assert not matches_pattern("agent:Run", "agent:RunAll")

    def test_star_matches_any_run_of_characters(self):
        assert matches_pattern("vrn:agent::*", "vrn:agent::deep-agent")
        assert matches_pattern("*", "anything at all")

    def test_star_also_matches_an_empty_run(self):
        assert matches_pattern("iam:*", "iam:")

    def test_question_mark_matches_exactly_one_character(self):
        assert matches_pattern("vrn:?", "vrn:a")
        assert not matches_pattern("vrn:?", "vrn:ab")

    def test_regex_metacharacters_are_literal(self):
        assert matches_pattern("vrn:a.b", "vrn:a.b")
        assert not matches_pattern("vrn:a.b", "vrn:axb")

    def test_square_brackets_are_literal_unlike_fnmatch(self):
        assert matches_pattern("vrn:[ab]", "vrn:[ab]")
        assert not matches_pattern("vrn:[ab]", "vrn:a")

    def test_a_trailing_newline_cannot_slip_past_a_literal(self):
        assert not matches_pattern("agent:Run", "agent:Run\n")

    def test_a_variable_is_replaced_by_its_value(self):
        assert matches_pattern(
            "vrn:session:${principal.id}:*", "vrn:session:42:session/x", {"principal.id": "42"}
        )

    def test_a_variable_does_not_match_someone_elses_value(self):
        assert not matches_pattern(
            "vrn:session:${principal.id}:*", "vrn:session:43:session/x", {"principal.id": "42"}
        )

    def test_an_unresolved_variable_matches_nothing(self):
        assert not matches_pattern("${principal.id}", "anything")
        assert not matches_pattern("vrn:session:${principal.id}:*", "vrn:session::x", {})

    def test_a_wildcard_inside_a_variable_value_stays_literal(self):
        assert not matches_pattern(
            "vrn:session:${principal.id}:x", "vrn:session:anyone:x", {"principal.id": "*"}
        )

    def test_matching_is_case_sensitive_by_default(self):
        assert not matches_pattern("vrn:agent::A", "vrn:agent::a")

    def test_case_insensitive_matching_is_available_for_actions(self):
        assert matches_pattern("agent:run", "agent:Run", case_sensitive = False)
