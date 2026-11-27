import os
import sys
import boto3
import argparse

from deploy.pipeline import DeploymentRecorder
from deploy.pipeline.commands.step_summary import write_summary


def main() -> int:
    parser = argparse.ArgumentParser(description = "Records that an environment was torn down.")
    parser.add_argument("--environment", required = True)
    parser.add_argument("--bucket", default = "vela47-artifacts")
    parser.add_argument("--region", default = "eu-central-1")
    arguments = parser.parse_args()

    run_url = f"{os.environ.get('GITHUB_SERVER_URL', '')}/{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}"
    record = DeploymentRecorder(boto3.client("s3", region_name = arguments.region), arguments.bucket).record_teardown(
        arguments.environment, run_url, os.environ.get("GITHUB_ACTOR", "unknown")
    )
    write_summary(f"### Teardown\n\n{arguments.environment} runs nothing now, its last release was {record['previous'] or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
