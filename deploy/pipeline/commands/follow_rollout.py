import sys
import boto3
import argparse
from datetime import datetime

from deploy.pipeline import SmokeTest
from deploy.pipeline import EcsRollout
from deploy.pipeline.commands.step_summary import write_summary


def main() -> int:
    parser = argparse.ArgumentParser(description = "Follows the ECS deployment of a release and smoke tests it.")
    parser.add_argument("--cluster", required = True)
    parser.add_argument("--service", required = True)
    parser.add_argument("--url", required = True, help = "Where the environment is served")
    parser.add_argument("--version", required = True, help = "The release the environment must report")
    parser.add_argument("--started-at", required = True, help = "ISO time just before the apply, in UTC")
    parser.add_argument("--region", default = "eu-central-1")
    arguments = parser.parse_args()

    rollout = EcsRollout(
        boto3.client("ecs", region_name = arguments.region),
        arguments.cluster,
        arguments.service,
        SmokeTest(arguments.url, arguments.version).run
    )
    problems = rollout.follow(datetime.fromisoformat(arguments.started_at))
    lines = [f"- {current}" for current in problems] or [f"- {arguments.url} runs {arguments.version}"]
    write_summary("### Rollout\n\n" + "\n".join(lines))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
