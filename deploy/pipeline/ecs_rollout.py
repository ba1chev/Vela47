import time
from datetime import datetime
from typing import Any, Callable, Optional

TERMINAL_FAILURES = {"ROLLBACK_SUCCESSFUL", "ROLLBACK_FAILED", "STOPPED"}
SMOKE_STAGE = "BAKE_TIME"


class EcsRollout:
    """Follows the deployment Terraform started on an ECS service until it ends, and runs
    the smoke test at the right moment. A CANARY deployment is smoke tested during its
    final bake time, once all traffic reaches the new tasks while the old ones are still
    kept, and a failure rolls it back at once. A ROLLING deployment has no bake time,
    so it is smoke tested once it succeeds and a failure only fails the pipeline.

    When the apply changed nothing ECS deploys (an infrastructure-only release), no new
    deployment shows up within new_deployment_seconds and only the smoke test runs."""

    def __init__(self, ecs: Any, cluster: str, service: str, smoke_test: Callable[[], list[str]],
        poll_seconds: float = 15.0, new_deployment_seconds: float = 90.0, timeout_seconds: float = 3600.0,
        log: Callable[[str], None] = print) -> None:
        self._ecs: Any = ecs
        self._cluster: str = cluster
        self._service: str = service
        self._smoke_test: Callable[[], list[str]] = smoke_test
        self._poll_seconds: float = poll_seconds
        self._new_deployment_seconds: float = new_deployment_seconds
        self._timeout_seconds: float = timeout_seconds
        self._log: Callable[[str], None] = log

    def _deployment_since(self, started_at: datetime) -> Optional[str]:
        response = self._ecs.list_service_deployments(
            cluster = self._cluster, service = self._service, createdAt = {"after": started_at}
        )
        deployments = sorted(response.get("serviceDeployments", []), key = lambda current: current["createdAt"])
        return deployments[-1]["serviceDeploymentArn"] if deployments else None

    def _describe(self, deployment_arn: str) -> dict[str, Any]:
        return self._ecs.describe_service_deployments(serviceDeploymentArns = [deployment_arn])["serviceDeployments"][0]

    @staticmethod
    def _fully_shifted(deployment: dict[str, Any]) -> bool:
        weight = deployment.get("targetServiceRevision", {}).get("requestedProductionTrafficWeight")
        return weight is None or weight >= 100

    def _smoke(self) -> list[str]:
        problems = self._smoke_test()
        self._log("Smoke test passed." if not problems else f"Smoke test failed: {'; '.join(problems)}")
        return problems

    def follow(self, started_at: datetime) -> list[str]:
        deadline = time.monotonic() + self._new_deployment_seconds
        deployment_arn = self._deployment_since(started_at)
        while deployment_arn is None and time.monotonic() < deadline:
            time.sleep(self._poll_seconds)
            deployment_arn = self._deployment_since(started_at)
        if deployment_arn is None:
            self._log("ECS has nothing new to deploy.")
            return self._smoke()

        deadline = time.monotonic() + self._timeout_seconds
        problems: list[str] = []
        smoked = False
        last_state = None
        while time.monotonic() < deadline:
            deployment = self._describe(deployment_arn)
            status, stage = deployment["status"], deployment.get("lifecycleStage")
            if (status, stage) != last_state:
                self._log(f"{status} {stage or ''}".strip())
                last_state = (status, stage)

            if status == "IN_PROGRESS" and stage == SMOKE_STAGE and self._fully_shifted(deployment) and not smoked:
                smoked = True
                problems = self._smoke()
                if problems:
                    self._ecs.stop_service_deployment(serviceDeploymentArn = deployment_arn, stopType = "ROLLBACK")
                    self._log("Rolling back.")
            elif status == "SUCCESSFUL":
                return problems if smoked else self._smoke()
            elif status in TERMINAL_FAILURES:
                return problems or [f"The deployment ended {status}: {deployment.get('statusReason', 'no reason given')}"]
            time.sleep(self._poll_seconds)
        return [f"The deployment did not finish within {int(self._timeout_seconds)} seconds."]
