from deploy.pipeline import PlanGuard
from deploy.pipeline import ReleaseManifest


def make_manifest(infrastructure = "none"):
    return ReleaseManifest(version = "1.1.0", infrastructure = infrastructure, database = "none", summary = "s")


def make_plan(*changes):
    return {"resource_changes": [
        {"address": address, "type": address.split(".")[-2], "change": {"actions": actions}}
        for address, actions in changes
    ]}


class TestPlanGuard:
    def test_a_plan_without_changes_passes_and_says_so(self):
        guard = PlanGuard(make_plan(("module.vpc.aws_vpc.this", ["no-op"])), "vpc", make_manifest())
        assert guard.violations() == [] and guard.summary() == "**vpc**: no changes"

    def test_the_app_root_changes_with_every_release(self):
        plan = make_plan(("module.app.aws_ecs_task_definition.this", ["delete", "create"]), ("module.app.aws_ecs_service.this", ["update"]))
        assert PlanGuard(plan, "app", make_manifest()).violations() == []

    def test_a_database_is_never_replaced_or_deleted_by_the_pipeline(self):
        plan = make_plan(("module.database.aws_db_instance.this", ["delete", "create"]))
        found = PlanGuard(plan, "database", make_manifest("breaking")).violations()
        assert found == ["module.database.aws_db_instance.this would be replaced; a database or a bucket is only ever removed by hand"]

    def test_an_undeclared_change_of_the_foundation_is_refused_as_drift(self):
        plan = make_plan(("module.vpc.aws_route.private_nat_gateway[0]", ["create"]))
        assert "infrastructure: none" in PlanGuard(plan, "vpc", make_manifest()).violations()[0]
        assert PlanGuard(plan, "vpc", make_manifest("additive")).violations() == []

    def test_removing_from_the_foundation_needs_a_breaking_release(self):
        plan = make_plan(("module.vpc.aws_nat_gateway.this[0]", ["delete"]))
        assert "only a breaking release" in PlanGuard(plan, "vpc", make_manifest("additive")).violations()[0]
        assert PlanGuard(plan, "vpc", make_manifest("breaking")).violations() == []

    def test_the_summary_lists_every_change(self):
        plan = make_plan(("module.app.aws_ecs_service.this", ["update"]), ("module.app.aws_lb.this", ["read"]))
        summary = PlanGuard(plan, "app", make_manifest()).summary()
        assert "1 changes" in summary and "| `module.app.aws_ecs_service.this` | update |" in summary
