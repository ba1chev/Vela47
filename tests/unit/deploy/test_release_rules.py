from deploy.pipeline import ReleaseRules
from deploy.pipeline import ReleaseManifest

APP = "app/server/server.py"
MODULE = "deploy/terraform/modules/app/main.tf"
MIGRATION = "db/migrations/versions/0002_add_column.py"


def make_manifest(version = "1.1.0", infrastructure = "none", database = "none"):
    return ReleaseManifest(version = version, infrastructure = infrastructure, database = database, summary = "s")


def violations(manifest, changed, base_version = "1.0.0", released = (1, 0, 0)):
    base = make_manifest(base_version) if base_version is not None else None
    return ReleaseRules(manifest, changed, base, released).violations()


class TestReleaseRules:
    def test_a_code_change_with_a_new_version_passes(self):
        assert violations(make_manifest(), [APP]) == []

    def test_a_code_change_without_a_new_version_fails(self):
        assert "needs a new version" in violations(make_manifest("1.0.0"), [APP])[0]

    def test_documentation_and_local_only_changes_need_no_release(self):
        changed = ["docs/release_process.md", "deploy/terraform/modules/app/README.md", "deploy/terraform/environments/local/docker/main.tf", "tests/unit/x.py"]
        rules = ReleaseRules(make_manifest("1.0.0"), changed, make_manifest("1.0.0"), (1, 0, 0))
        assert not rules.releases and rules.violations() == []

    def test_a_new_version_must_be_above_the_released_one(self):
        assert "not above 1.0.0" in violations(make_manifest("0.9.0"), [APP], base_version = "0.8.0")[0]

    def test_terraform_changes_must_be_declared(self):
        assert "need infrastructure" in violations(make_manifest(), [MODULE])[0]
        assert violations(make_manifest(infrastructure = "additive"), [MODULE]) == []

    def test_a_declared_infrastructure_change_needs_terraform_changes(self):
        assert "no Terraform" in violations(make_manifest(infrastructure = "additive"), [APP])[0]

    def test_migrations_must_be_declared_and_declarations_need_migrations(self):
        assert "need database" in violations(make_manifest(), [MIGRATION])[0]
        assert "no migration" in violations(make_manifest(database = "expand"), [APP])[0]
        assert violations(make_manifest(database = "expand"), [MIGRATION, APP]) == []

    def test_a_breaking_infrastructure_change_ships_alone_as_a_major_version(self):
        found = violations(make_manifest(infrastructure = "breaking"), [MODULE, APP])
        assert any("without code changes" in current for current in found)
        assert any("new major version" in current for current in found)
        assert violations(make_manifest("2.0.0", infrastructure = "breaking"), [MODULE]) == []

    def test_a_contract_migration_ships_without_code(self):
        found = violations(make_manifest("2.0.0", database = "contract"), [MIGRATION, "db/tables/chat_session_table.py"])
        assert found == ["A contract migration ships without code changes, found db/tables/chat_session_table.py."]

    def test_the_first_release_has_nothing_to_compare_with(self):
        assert violations(make_manifest("1.0.0", "additive", "expand"), [MODULE, MIGRATION], base_version = None, released = None) == []

    def test_the_modules_of_the_shared_roots_are_applied_by_hand_and_need_no_release(self):
        changed = ["deploy/terraform/modules/ci_role/main.tf", "deploy/terraform/modules/ecr/main.tf"]
        rules = ReleaseRules(make_manifest("1.0.0"), changed, make_manifest("1.0.0"), (1, 0, 0))
        assert not rules.releases and rules.violations() == []
