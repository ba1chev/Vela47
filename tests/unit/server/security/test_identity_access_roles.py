from app.server.security import IdentityAccessRequest
from app.server.security import IdentityAccessRoleType
from app.server.security import IdentityAccessPolicyEffect
from app.server.security import IDENTITY_ACCESS_ROLE_REGISTRY

ALLOW = IdentityAccessPolicyEffect.ALLOW
DENY = IdentityAccessPolicyEffect.DENY


def make_role(role_type):
    return IDENTITY_ACCESS_ROLE_REGISTRY[role_type]()


def trust_verdict(role_type, entity_vrn):
    role = make_role(role_type)
    return role.trust_policy.evaluate(IdentityAccessRequest(
        principals = [entity_vrn], action = "iam:AssumeRole", resource = role.vrn
    ))


def permission_verdicts(role_type, action, resource):
    role = make_role(role_type)
    request = IdentityAccessRequest(
        principals = ["vrn:iam::entity/x/1", role.vrn],
        action = action,
        resource = resource,
        variables = {"principal.id": "1"}
    )
    return [current_policy.evaluate(request) for current_policy in role.permission_policies]


class TestIdentityAccessRoles:
    def test_every_role_type_is_registered(self):
        assert set(IDENTITY_ACCESS_ROLE_REGISTRY) == set(IdentityAccessRoleType)

    def test_each_registered_role_reports_its_own_type(self):
        for current_type in IdentityAccessRoleType:
            assert make_role(current_type).role_type is current_type

    def test_the_role_vrn_names_the_role(self):
        assert make_role(IdentityAccessRoleType.ADMIN).vrn == "vrn:iam::role/admin"

    def test_admin_trusts_admins_and_nobody_else(self):
        assert trust_verdict(IdentityAccessRoleType.ADMIN, "vrn:iam::entity/admin/1") is ALLOW
        assert trust_verdict(IdentityAccessRoleType.ADMIN, "vrn:iam::entity/user/1") is None
        assert trust_verdict(IdentityAccessRoleType.ADMIN, "vrn:iam::entity/guest/1") is None

    def test_user_trusts_users_and_admins(self):
        assert trust_verdict(IdentityAccessRoleType.USER, "vrn:iam::entity/user/1") is ALLOW
        assert trust_verdict(IdentityAccessRoleType.USER, "vrn:iam::entity/admin/1") is ALLOW
        assert trust_verdict(IdentityAccessRoleType.USER, "vrn:iam::entity/guest/1") is None

    def test_guest_trusts_guests_only(self):
        assert trust_verdict(IdentityAccessRoleType.GUEST, "vrn:iam::entity/guest/1") is ALLOW
        assert trust_verdict(IdentityAccessRoleType.GUEST, "vrn:iam::entity/user/1") is None

    def test_admin_may_do_anything(self):
        assert ALLOW in permission_verdicts(IdentityAccessRoleType.ADMIN, "iam:CreateEntity", "vrn:iam::entity/user")
        assert ALLOW in permission_verdicts(IdentityAccessRoleType.ADMIN, "agent:Run", "vrn:agent::deep-agent")

    def test_user_may_run_agents(self):
        assert ALLOW in permission_verdicts(IdentityAccessRoleType.USER, "agent:Run", "vrn:agent::deep-agent")

    def test_user_is_silent_on_identity_which_makes_it_an_implicit_deny(self):
        verdicts = permission_verdicts(IdentityAccessRoleType.USER, "iam:CreateEntity", "vrn:iam::entity/user")
        assert ALLOW not in verdicts and DENY not in verdicts

    def test_guest_may_run_agents(self):
        assert ALLOW in permission_verdicts(IdentityAccessRoleType.GUEST, "agent:Run", "vrn:agent::deep-agent")

    def test_guest_is_explicitly_denied_identity(self):
        assert DENY in permission_verdicts(IdentityAccessRoleType.GUEST, "iam:CreateEntity", "vrn:iam::entity/user")

    def test_user_may_do_anything_with_their_own_conversations(self):
        for current_action in ["session:Create", "session:List", "session:Read", "session:Write", "session:Delete"]:
            assert ALLOW in permission_verdicts(IdentityAccessRoleType.USER, current_action, "vrn:session:1:session/a")
        assert ALLOW in permission_verdicts(IdentityAccessRoleType.USER, "session:List", "vrn:session:1:session")

    def test_user_is_silent_on_someone_elses_conversations(self):
        verdicts = permission_verdicts(IdentityAccessRoleType.USER, "session:Read", "vrn:session:2:session/a")
        assert ALLOW not in verdicts and DENY not in verdicts

    def test_guest_keeps_conversations_of_its_own_too(self):
        assert ALLOW in permission_verdicts(IdentityAccessRoleType.GUEST, "session:Write", "vrn:session:1:session/a")
        assert ALLOW not in permission_verdicts(IdentityAccessRoleType.GUEST, "session:Read", "vrn:session:2:session/a")

    def test_users_and_guests_own_their_documents_and_nobody_elses(self):
        for current_role in [IdentityAccessRoleType.USER, IdentityAccessRoleType.GUEST]:
            for current_action in ["knowledge:Upload", "knowledge:List", "knowledge:Delete", "knowledge:Search"]:
                assert ALLOW in permission_verdicts(current_role, current_action, "vrn:knowledge:1:document/d")
            assert ALLOW not in permission_verdicts(current_role, "knowledge:Delete", "vrn:knowledge:2:document/d")

    def test_both_agents_may_be_run_by_users_and_guests(self):
        for current_role in [IdentityAccessRoleType.USER, IdentityAccessRoleType.GUEST]:
            assert ALLOW in permission_verdicts(current_role, "agent:Run", "vrn:agent::rag-agent")

    def test_admin_may_read_anyones_conversation(self):
        assert ALLOW in permission_verdicts(IdentityAccessRoleType.ADMIN, "session:Read", "vrn:session:2:session/a")

    def test_admin_sessions_are_the_shortest(self):
        lengths = {current_type: make_role(current_type).max_session_seconds for current_type in IdentityAccessRoleType}
        assert lengths[IdentityAccessRoleType.ADMIN] == min(lengths.values())
