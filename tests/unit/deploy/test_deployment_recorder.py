import yaml
from datetime import datetime, timezone

from deploy.pipeline import DeploymentRecorder
from tests.fixtures.deploy.in_memory_s3_client import InMemoryS3Client


def record(recorder, version, succeeded = True, minute = 0):
    return recorder.record("prod", version, "abc1234", succeeded, "https://github.com/run/1", "ba1chev", datetime(2026, 11, 26, 10, minute, tzinfo = timezone.utc))


class TestDeploymentRecorder:
    def test_the_first_deployment_has_no_previous_release(self):
        recorder = DeploymentRecorder(InMemoryS3Client(), "vela47-artifacts")
        record(recorder, "1.0.0")
        assert recorder.current("prod")["version"] == "1.0.0" and recorder.current("prod")["previous"] is None

    def test_a_new_release_remembers_the_one_a_rollback_would_return_to(self):
        recorder = DeploymentRecorder(InMemoryS3Client(), "vela47-artifacts")
        record(recorder, "1.0.0")
        record(recorder, "1.1.0", minute = 1)
        assert recorder.current("prod")["previous"] == "1.0.0"

    def test_a_failed_deployment_is_kept_in_the_history_but_does_not_become_current(self):
        s3 = InMemoryS3Client()
        recorder = DeploymentRecorder(s3, "vela47-artifacts")
        record(recorder, "1.0.0")
        record(recorder, "1.1.0", succeeded = False, minute = 1)
        failed = yaml.safe_load(s3.objects[("vela47-artifacts", "deployments/prod/history/20261126T100100Z-1.1.0.yaml")])
        assert failed["outcome"] == "failed" and recorder.current("prod")["version"] == "1.0.0"

    def test_redeploying_the_same_release_keeps_its_previous(self):
        recorder = DeploymentRecorder(InMemoryS3Client(), "vela47-artifacts")
        record(recorder, "1.0.0")
        record(recorder, "1.1.0", minute = 1)
        record(recorder, "1.1.0", minute = 2)
        assert recorder.current("prod")["previous"] == "1.0.0"

    def test_a_release_is_promoted_only_after_it_succeeded_in_the_environment_before(self):
        recorder = DeploymentRecorder(InMemoryS3Client(), "vela47-artifacts")
        recorder.record("dev", "1.1.0", "abc1234", True, "run", "ci")
        recorder.record("staging", "1.1.0", "abc1234", False, "run", "ci")
        assert recorder.may_promote("dev", "1.1.0") and recorder.may_promote("staging", "1.1.0")
        assert not recorder.may_promote("prod", "1.1.0") and not recorder.may_promote("staging", "1.2.0")
