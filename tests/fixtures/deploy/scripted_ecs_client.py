from datetime import datetime, timezone


class ScriptedEcsClient:
    """Stands in for the boto3 ECS client during a rollout: lists one deployment, or none,
    and answers every describe with the next state of a script, repeating the last one.
    Records every rollback it is asked for, so a test sees what EcsRollout did to ECS."""

    def __init__(self, states, appears_after = 0) -> None:
        self.rollbacks = []
        self.listings = 0
        self._states = list(states)
        self._appears_after = appears_after

    def list_service_deployments(self, cluster, service, createdAt):
        self.listings += 1
        if not self._states or self.listings <= self._appears_after:
            return {"serviceDeployments": []}
        return {"serviceDeployments": [{"serviceDeploymentArn": "arn:deployment/1", "createdAt": datetime.now(timezone.utc)}]}

    def describe_service_deployments(self, serviceDeploymentArns):
        state = self._states.pop(0) if len(self._states) > 1 else self._states[0]
        if self.rollbacks and state["status"] == "IN_PROGRESS":
            state = {"status": "ROLLBACK_SUCCESSFUL"}
        return {"serviceDeployments": [dict(state, serviceDeploymentArn = serviceDeploymentArns[0])]}

    def stop_service_deployment(self, serviceDeploymentArn, stopType):
        self.rollbacks.append((serviceDeploymentArn, stopType))
