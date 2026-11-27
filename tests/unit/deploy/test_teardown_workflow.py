import yaml
import pathlib

WORKFLOWS = pathlib.Path(__file__).resolve().parents[3] / ".github" / "workflows"
TEARDOWN = yaml.safe_load((WORKFLOWS / "teardown.yaml").read_text())
DEPLOYMENT = yaml.safe_load((WORKFLOWS / "deployment.yaml").read_text())
TRIGGERS = TEARDOWN[True]
JOB = TEARDOWN["jobs"]["teardown"]


class TestTeardownWorkflow:
    def test_it_is_only_ever_started_by_hand(self):
        assert list(TRIGGERS) == ["workflow_dispatch"]

    def test_only_the_owner_tears_down_and_only_from_main(self):
        assert "github.actor == github.repository_owner" in JOB["if"] and "github.ref == 'refs/heads/main'" in JOB["if"]

    def test_the_environment_has_to_be_typed_twice(self):
        first = JOB["steps"][0]
        assert first["name"] == "Check the confirmation" and '"$CONFIRM" != "$ENVIRONMENT"' in first["run"]

    def test_staging_and_prod_wait_for_the_approval_of_their_environment(self):
        assert JOB["environment"] == "${{ inputs.environment }}"

    def test_it_never_runs_at_the_same_time_as_a_deployment_of_the_environment(self):
        assert TEARDOWN["concurrency"]["group"] == DEPLOYMENT["concurrency"]["group"]
        assert TRIGGERS["workflow_dispatch"]["inputs"]["environment"]["options"] == DEPLOYMENT[True]["workflow_dispatch"]["inputs"]["environment"]["options"]

    def test_it_destroys_in_the_reverse_order_of_a_deployment(self):
        roots = [current["run"].split('"$ROOTS/')[1].split('"')[0] for current in JOB["steps"] if "teardown_root.sh" in current.get("run", "")]
        assert roots == ["app", "database", "vpc/eu-central-1"]
