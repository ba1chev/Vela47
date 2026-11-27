from typing import Any, Optional

from deploy.pipeline import ReleaseManifest

RELEASES_PREFIX = "releases/"


class ReleaseCatalog:
    """Lists the releases the delivery workflow stored in the artifacts bucket, one
    releases/<version>/ prefix each. A teardown runs the Terraform of the release an
    environment runs; an environment that runs none, because it was never deployed or
    already torn down, is handled with the newest release, whose state is empty anyway."""

    def __init__(self, s3: Any, bucket: str) -> None:
        self._s3: Any = s3
        self._bucket: str = bucket

    def versions(self) -> list[str]:
        listing = self._s3.list_objects_v2(Bucket = self._bucket, Prefix = RELEASES_PREFIX, Delimiter = "/")
        names = [current["Prefix"][len(RELEASES_PREFIX):].rstrip("/") for current in listing.get("CommonPrefixes", [])]
        return sorted(
            (current for current in names if ReleaseManifest.parse_version(current) is not None),
            key = ReleaseManifest.parse_version
        )

    def newest(self) -> Optional[str]:
        versions = self.versions()
        return versions[-1] if versions else None
