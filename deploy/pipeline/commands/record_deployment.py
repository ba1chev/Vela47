import os
import sys
import boto3
import argparse

from deploy.pipeline import DeploymentRecorder
from deploy.pipeline.commands.step_summary import write_summary


def main() -> int:
    parser = argparse.ArgumentParser(description = "Records a deployment in the artifacts bucket.")
    parser.add_argument("--environment", required = True)
    parser.add_argument("--version", required = True)
    parser.add_argument("--commit", required = True)
    parser.add_argument("--outcome", required = True, choices = ["succeeded", "failed"])
    parser.add_argument("--bucket", default = "vela47-artifacts")
    parser.add_argument("--region", default = "eu-central-1")
    arguments = parser.parse_args()

    run_url = f"{os.environ.get('GITHUB_SERVER_URL', '')}/{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}"
    record = DeploymentRecorder(boto3.client("s3", region_name = arguments.region), arguments.bucket).record(
        arguments.environment, arguments.version, arguments.commit, arguments.outcome == "succeeded",
        run_url, os.environ.get("GITHUB_ACTOR", "unknown")
    )
    write_summary(
        f"### Deployment record\n\n{arguments.environment}: {record['version']} {record['outcome']}, "
        f"previous {record['previous'] or 'none'}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
