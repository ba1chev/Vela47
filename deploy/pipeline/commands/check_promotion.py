import sys
import boto3
import argparse

from deploy.pipeline import PROMOTIONS
from deploy.pipeline import DeploymentRecorder


def main() -> int:
    parser = argparse.ArgumentParser(description = "Refuses a release the environment before has not run successfully.")
    parser.add_argument("--environment", required = True)
    parser.add_argument("--version", required = True)
    parser.add_argument("--bucket", default = "vela47-artifacts")
    parser.add_argument("--region", default = "eu-central-1")
    arguments = parser.parse_args()

    recorder = DeploymentRecorder(boto3.client("s3", region_name = arguments.region), arguments.bucket)
    if recorder.may_promote(arguments.environment, arguments.version):
        return 0
    print(
        f"::error::{arguments.version} has not been deployed to {PROMOTIONS[arguments.environment]} successfully, "
        f"so it may not go to {arguments.environment}."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
