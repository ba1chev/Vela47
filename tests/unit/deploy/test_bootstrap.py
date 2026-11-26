import re
import pathlib

REPOSITORY = pathlib.Path(__file__).resolve().parents[3]
BOOTSTRAP = (REPOSITORY / "deploy" / "bootstrap.sh").read_text()
WORKFLOWS = REPOSITORY / ".github" / "workflows"


def value(name):
    return re.search(rf'^{name}="?([^"\n]+)"?$', BOOTSTRAP, re.MULTILINE).group(1)


class TestBootstrap:
    def test_the_role_trusts_main_and_every_environment_a_deploy_job_runs_in(self):
        deployment = (WORKFLOWS / "deployment.yaml").read_text()
        environments = re.search(r"options: \[([^\]]+)\]", deployment).group(1).replace(" ", "").split(",")
        prefix = "$SUBJECT_PREFIX"
        assert f'"{prefix}:ref:refs/heads/main"' in BOOTSTRAP
        assert all(f'"{prefix}:environment:{current}"' in BOOTSTRAP for current in environments)

    def test_the_trusted_subject_is_the_immutable_one_of_this_repository(self):
        assert value("SUBJECT_PREFIX") in (REPOSITORY / "docs" / "open_id_connect.md").read_text()

    def test_a_session_lasts_as_long_as_the_longest_job_asks_for(self):
        asked = [int(current) for current in re.findall(r"role-duration-seconds: (\d+)", (WORKFLOWS / "deployment.yaml").read_text())]
        assert asked and max(asked) <= int(value("SESSION_SECONDS"))

    def test_it_creates_the_bucket_every_backend_uses(self):
        backend = (REPOSITORY / "deploy" / "terraform" / "environments" / "shared" / "s3_state" / "state.tf").read_text()
        assert f'bucket       = "{value("STATE_BUCKET")}"' in backend

    def test_it_applies_every_shared_root(self):
        shared = REPOSITORY / "deploy" / "terraform" / "environments" / "shared"
        roots = {current.name for current in shared.iterdir() if (current / "main.tf").exists()}
        assert roots == {"s3_state", "iam", "artifacts", "ecr"}
        assert "for root in iam artifacts ecr; do" in BOOTSTRAP and '"$SHARED/s3_state"' in BOOTSTRAP
