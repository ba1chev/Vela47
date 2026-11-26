from typing import Any

from deploy.pipeline import ReleaseManifest
from deploy.pipeline import InfrastructureChange

PROTECTED_RESOURCE_TYPES = {"aws_db_instance", "aws_s3_bucket"}
FOUNDATION_ROOTS = {"vpc", "database"}
QUIET_ACTIONS = {"no-op", "read"}


class PlanGuard:
    """Reads a saved Terraform plan (terraform show -json) of one root module before the
    deployment applies it, and refuses what the release did not declare. No plan may
    delete or replace a database or a bucket: that is done by hand, after a backup. The
    vpc and database roots change only in a release that declares an infrastructure
    change, which also catches drift made outside Terraform, and delete something only
    in a breaking one. The app root changes with every release, since its task
    definition carries the new image, and so does any root on its first deployment."""

    def __init__(self, plan: dict[str, Any], root: str, manifest: ReleaseManifest) -> None:
        self._changes: list[dict[str, Any]] = [
            current for current in plan.get("resource_changes", [])
            if set(current["change"]["actions"]) - QUIET_ACTIONS
        ]
        self._root: str = root
        self._manifest: ReleaseManifest = manifest
        self._first_deployment: bool = not self._managed_resources(
            plan.get("prior_state", {}).get("values", {}).get("root_module", {})
        )

    @classmethod
    def _managed_resources(cls, module: dict[str, Any]) -> int:
        return (
            sum(1 for current in module.get("resources", []) if current.get("mode") == "managed")
            + sum(cls._managed_resources(current) for current in module.get("child_modules", []))
        )

    @property
    def first_deployment(self) -> bool:
        return self._first_deployment

    @property
    def changes(self) -> list[tuple[str, str]]:
        return [(current["address"], "/".join(current["change"]["actions"])) for current in self._changes]

    def violations(self) -> list[str]:
        found = [
            f"{current['address']} would be {'replaced' if 'create' in current['change']['actions'] else 'deleted'}; "
            "a database or a bucket is only ever removed by hand"
            for current in self._changes
            if current["type"] in PROTECTED_RESOURCE_TYPES and "delete" in current["change"]["actions"]
        ]
        if self._root not in FOUNDATION_ROOTS or self._first_deployment:
            return found

        if self._changes and self._manifest.infrastructure is InfrastructureChange.NONE:
            found.append(
                f"The {self._root} root would change {len(self._changes)} resources, but the release declares "
                "infrastructure: none. Either the release is missing its declaration or someone changed the "
                "environment outside Terraform."
            )
        deleted = [current["address"] for current in self._changes if "delete" in current["change"]["actions"]]
        if deleted and self._manifest.infrastructure is not InfrastructureChange.BREAKING:
            found.append(f"{', '.join(deleted)} would be deleted or replaced, which only a breaking release may do.")
        return found

    def summary(self) -> str:
        if not self._changes:
            return f"**{self._root}**: no changes"
        rows = "\n".join(f"| `{address}` | {actions} |" for address, actions in self.changes)
        first = ", first deployment" if self._first_deployment else ""
        return f"**{self._root}**: {len(self._changes)} changes{first}\n\n| Resource | Actions |\n|---|---|\n{rows}"
