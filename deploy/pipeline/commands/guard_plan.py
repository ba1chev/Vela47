import sys
import json
import argparse

from deploy.pipeline import PlanGuard
from deploy.pipeline import ReleaseArtifact
from deploy.pipeline.commands.step_summary import write_summary


def main() -> int:
    parser = argparse.ArgumentParser(description = "Refuses a Terraform plan that does more than the release declares.")
    parser.add_argument("--plan", required = True, help = "Output of terraform show -json <plan>")
    parser.add_argument("--root", required = True, choices = ["vpc", "database", "app"])
    parser.add_argument("--release", required = True, help = "The release.yaml of the release being deployed")
    arguments = parser.parse_args()

    with open(arguments.plan, encoding = "utf-8") as plan, open(arguments.release, encoding = "utf-8") as release:
        guard = PlanGuard(json.load(plan), arguments.root, ReleaseArtifact.from_yaml(release.read()).manifest)
    violations = guard.violations()

    summary = guard.summary() + "".join(f"\n\n:x: {current}" for current in violations)
    print(summary)
    write_summary(summary)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
