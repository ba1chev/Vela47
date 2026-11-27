import sys
import boto3
import argparse

from deploy.pipeline import ReleaseCatalog
from deploy.pipeline import DeploymentRecorder


def main() -> int:
    parser = argparse.ArgumentParser(description = "Prints the release whose Terraform a teardown of an environment runs.")
    parser.add_argument("--environment", required = True)
    parser.add_argument("--bucket", default = "vela47-artifacts")
    parser.add_argument("--region", default = "eu-central-1")
    arguments = parser.parse_args()

    s3 = boto3.client("s3", region_name = arguments.region)
    current = DeploymentRecorder(s3, arguments.bucket).current(arguments.environment) or {}
    version = current.get("version") or ReleaseCatalog(s3, arguments.bucket).newest()
    if version is None:
        print("::error::No release is stored, so there is nothing an environment could run.")
        return 1
    print(version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
