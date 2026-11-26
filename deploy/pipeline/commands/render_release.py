import sys
import argparse
from datetime import datetime, timezone

from deploy.pipeline import ReleaseArtifact
from deploy.pipeline import ReleaseManifest


def main() -> int:
    parser = argparse.ArgumentParser(description = "Writes the release.yaml the delivery workflow stores with a release.")
    parser.add_argument("--commit", required = True)
    parser.add_argument("--app-image", required = True, help = "ECR URI of the server image, pinned by digest")
    parser.add_argument("--sandbox-image", required = True, help = "ECR URI of the sandbox image, pinned by digest")
    parser.add_argument("--output", required = True)
    arguments = parser.parse_args()

    artifact = ReleaseArtifact(
        manifest = ReleaseManifest.load(),
        commit = arguments.commit,
        created_at = datetime.now(timezone.utc),
        images = {"app": arguments.app_image, "sandbox": arguments.sandbox_image}
    )
    with open(arguments.output, "w", encoding = "utf-8") as output:
        output.write(artifact.to_yaml())
    print(artifact.to_yaml())
    return 0


if __name__ == "__main__":
    sys.exit(main())
