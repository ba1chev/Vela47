import yaml
from typing import Any, Optional
from datetime import datetime, timezone

DEPLOYMENTS_PREFIX = "deployments"


PROMOTIONS = {"staging": "dev", "prod": "staging"}


class DeploymentRecorder:
    """Keeps the record of what each environment runs in the artifacts bucket:
    deployments/<environment>/current.yaml names the release it runs and the one before,
    which is what a rollback redeploys, and every attempt, failed or not, is kept under
    deployments/<environment>/history/. Only a successful deployment or a teardown moves
    current.yaml; after a teardown it runs no release and remembers the last one. A release
    reaches staging only after it succeeded in dev, and prod only after staging, which
    the history answers."""

    def __init__(self, s3: Any, bucket: str) -> None:
        self._s3: Any = s3
        self._bucket: str = bucket

    def _key(self, environment: str, name: str) -> str:
        return f"{DEPLOYMENTS_PREFIX}/{environment}/{name}"

    def current(self, environment: str) -> Optional[dict[str, Any]]:
        try:
            body = self._s3.get_object(Bucket = self._bucket, Key = self._key(environment, "current.yaml"))["Body"].read()
        except self._s3.exceptions.NoSuchKey:
            return None
        return yaml.safe_load(body)

    def succeeded(self, environment: str, version: str) -> bool:
        listing = self._s3.list_objects_v2(Bucket = self._bucket, Prefix = self._key(environment, "history/"))
        keys = [current["Key"] for current in listing.get("Contents", []) if current["Key"].endswith(f"-{version}.yaml")]
        return any(
            yaml.safe_load(self._s3.get_object(Bucket = self._bucket, Key = current)["Body"].read())["outcome"] == "succeeded"
            for current in keys
        )

    def may_promote(self, environment: str, version: str) -> bool:
        before = PROMOTIONS.get(environment)
        return before is None or self.succeeded(before, version)

    def _put(self, key: str, document: dict[str, Any]) -> None:
        self._s3.put_object(
            Bucket = self._bucket, Key = key, Body = yaml.safe_dump(document, sort_keys = False).encode(),
            ContentType = "text/yaml"
        )

    def record(self, environment: str, version: str, commit: str, succeeded: bool, run_url: str,
        actor: str, now: Optional[datetime] = None) -> dict[str, Any]:
        now = now or datetime.now(timezone.utc)
        current = self.current(environment) or {}
        last = current.get("version")
        document = {
            "environment": environment,
            "version": version,
            "previous": last if last and last != version else current.get("previous"),
            "commit": commit,
            "outcome": "succeeded" if succeeded else "failed",
            "deployed_at": now.isoformat(),
            "run": run_url,
            "actor": actor
        }
        self._put(self._key(environment, f"history/{now.strftime('%Y%m%dT%H%M%SZ')}-{version}.yaml"), document)
        if succeeded:
            self._put(self._key(environment, "current.yaml"), document)
        return document

    def record_teardown(self, environment: str, run_url: str, actor: str,
        now: Optional[datetime] = None) -> dict[str, Any]:
        now = now or datetime.now(timezone.utc)
        current = self.current(environment) or {}
        document = {
            "environment": environment,
            "version": None,
            "previous": current.get("version") or current.get("previous"),
            "commit": None,
            "outcome": "torn_down",
            "deployed_at": now.isoformat(),
            "run": run_url,
            "actor": actor
        }
        self._put(self._key(environment, f"history/{now.strftime('%Y%m%dT%H%M%SZ')}-teardown.yaml"), document)
        self._put(self._key(environment, "current.yaml"), document)
        return document
