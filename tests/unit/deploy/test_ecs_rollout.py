from datetime import datetime, timezone

from deploy.pipeline import EcsRollout
from tests.fixtures.deploy.scripted_ecs_client import ScriptedEcsClient


def follow(states, smoke_problems = (), appears_after = 0):
    ecs = ScriptedEcsClient(states, appears_after)
    smoked = []

    def smoke_test():
        smoked.append(True)
        return list(smoke_problems)

    rollout = EcsRollout(ecs, "vela47-prod", "vela47-prod-app", smoke_test, poll_seconds = 0, new_deployment_seconds = 0, log = lambda message: None)
    return rollout.follow(datetime.now(timezone.utc)), ecs, smoked


CANARY = [
    {"status": "IN_PROGRESS", "lifecycleStage": "SCALE_UP"},
    {"status": "IN_PROGRESS", "lifecycleStage": "PRODUCTION_TRAFFIC_SHIFT", "targetServiceRevision": {"requestedProductionTrafficWeight": 10}},
    {"status": "IN_PROGRESS", "lifecycleStage": "BAKE_TIME", "targetServiceRevision": {"requestedProductionTrafficWeight": 100}},
    {"status": "SUCCESSFUL"},
]


class TestEcsRollout:
    def test_a_canary_is_smoke_tested_once_during_its_bake_time(self):
        problems, ecs, smoked = follow(CANARY)
        assert problems == [] and smoked == [True] and ecs.rollbacks == []

    def test_a_canary_that_fails_its_smoke_test_is_rolled_back(self):
        problems, ecs, _ = follow(CANARY, smoke_problems = ["the health endpoint answered 502"])
        assert problems == ["the health endpoint answered 502"]
        assert ecs.rollbacks == [("arn:deployment/1", "ROLLBACK")]

    def test_the_canary_share_of_the_traffic_is_not_smoke_tested(self):
        states = [{"status": "IN_PROGRESS", "lifecycleStage": "BAKE_TIME", "targetServiceRevision": {"requestedProductionTrafficWeight": 10}}, {"status": "SUCCESSFUL"}]
        _, _, smoked = follow(states)
        assert smoked == [True]

    def test_a_rolling_deployment_is_smoke_tested_once_it_succeeds(self):
        problems, ecs, smoked = follow([{"status": "IN_PROGRESS", "lifecycleStage": "SCALE_UP"}, {"status": "SUCCESSFUL"}])
        assert problems == [] and smoked == [True] and ecs.rollbacks == []

    def test_a_deployment_ecs_rolled_back_fails_with_its_reason(self):
        problems, _, smoked = follow([{"status": "ROLLBACK_SUCCESSFUL", "statusReason": "alarm vela47-prod-app-5xx"}])
        assert problems == ["The deployment ended ROLLBACK_SUCCESSFUL: alarm vela47-prod-app-5xx"] and smoked == []

    def test_an_apply_that_deploys_nothing_is_only_smoke_tested(self):
        problems, _, smoked = follow([])
        assert problems == [] and smoked == [True]
