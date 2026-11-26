from typing import Optional

from deploy.pipeline import DatabaseChange
from deploy.pipeline import ReleaseManifest
from deploy.pipeline import InfrastructureChange

RELEASED_PREFIXES = ("app/", "db/", "deploy/images/aws/", "deploy/pipeline/", "deploy/terraform/modules/")
RELEASED_FILES = ("requirements.txt",)
AWS_ENVIRONMENT_PREFIXES = tuple(f"deploy/terraform/environments/{current}/" for current in ("dev", "staging", "prod"))
INFRASTRUCTURE_PREFIXES = ("deploy/terraform/modules/",) + AWS_ENVIRONMENT_PREFIXES
LOCAL_ONLY_MODULES = ("deploy/terraform/modules/docker_app/", "deploy/terraform/modules/docker_database/")
MIGRATION_PREFIX = "db/migrations/versions/"
CODE_PREFIXES = ("app/", "db/")


class ReleaseRules:
    """Holds a pull request to what deploy/release.yaml declares about it, given the paths
    it changes, the manifest on main and the newest version already released. A change
    to what runs on AWS needs a new version above every released one; Terraform changes
    need an infrastructure change and migrations a database change, and a new release
    declares only changes it makes. A breaking change or a contract migration ships
    without code and as a new major version, so a release never removes something the
    release before it still uses."""

    def __init__(self, manifest: ReleaseManifest, changed_paths: list[str],
        base_manifest: Optional[ReleaseManifest], released_version: Optional[tuple[int, int, int]]) -> None:
        self._manifest: ReleaseManifest = manifest
        self._changed_paths: list[str] = [current for current in changed_paths if not current.endswith(".md")]
        self._base_manifest: Optional[ReleaseManifest] = base_manifest
        self._released_version: Optional[tuple[int, int, int]] = released_version

    def _changed(self, prefixes: tuple[str, ...], excluded: tuple[str, ...] = ()) -> list[str]:
        return [
            current for current in self._changed_paths
            if current.startswith(prefixes) and not current.startswith(excluded)
        ]

    @property
    def declares_release(self) -> bool:
        return self._base_manifest is None or self._manifest.version != self._base_manifest.version

    @property
    def releases(self) -> bool:
        return bool(
            self._changed(RELEASED_PREFIXES + AWS_ENVIRONMENT_PREFIXES, LOCAL_ONLY_MODULES)
            or any(current in RELEASED_FILES for current in self._changed_paths)
        )

    def violations(self) -> list[str]:
        manifest = self._manifest
        infrastructure = self._changed(INFRASTRUCTURE_PREFIXES, LOCAL_ONLY_MODULES)
        migrations = self._changed((MIGRATION_PREFIX,))
        code = self._changed(CODE_PREFIXES, (MIGRATION_PREFIX,))
        found = []

        if self.releases and not self.declares_release:
            found.append(f"The pull request changes what runs on AWS, so deploy/release.yaml needs a new version, not {manifest.version}.")
        if self.declares_release and self._released_version is not None and manifest.version_key <= self._released_version:
            found.append(
                f"Version {manifest.version} is not above {'.'.join(map(str, self._released_version))}, "
                "the newest released version."
            )
        if infrastructure and manifest.infrastructure is InfrastructureChange.NONE:
            found.append(f"Terraform changes ({infrastructure[0]} and {len(infrastructure) - 1} more) need infrastructure: additive or breaking.")
        if self.declares_release and not infrastructure and manifest.infrastructure is not InfrastructureChange.NONE:
            found.append(f"infrastructure: {manifest.infrastructure.value} is declared, but no Terraform of the AWS environments changes.")
        if migrations and manifest.database is DatabaseChange.NONE:
            found.append(f"New migrations ({migrations[0]}) need database: expand or contract.")
        if self.declares_release and not migrations and manifest.database is not DatabaseChange.NONE:
            found.append(f"database: {manifest.database.value} is declared, but no migration changes.")
        if manifest.infrastructure is InfrastructureChange.BREAKING and code:
            found.append(f"A breaking infrastructure change ships without code changes, found {code[0]}.")
        if manifest.database is DatabaseChange.CONTRACT and code:
            found.append(f"A contract migration ships without code changes, found {code[0]}.")
        if manifest.breaking and self._released_version is not None and manifest.version_key[0] <= self._released_version[0]:
            found.append(f"A breaking change or a contract migration needs a new major version, not {manifest.version}.")
        return found
