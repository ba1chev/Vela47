import sys
import argparse
import subprocess

from deploy.pipeline import ReleaseRules
from deploy.pipeline import ReleaseManifest
from deploy.pipeline.commands.step_summary import write_summary

MANIFEST = "deploy/release.yaml"


def _git(*arguments: str) -> str:
    return subprocess.run(["git", *arguments], capture_output = True, text = True, check = True).stdout


def _released_version() -> tuple[int, int, int] | None:
    tags = [current.strip() for current in _git("tag", "--list", "v*", "--sort=-v:refname").splitlines() if current.strip()]
    versions = [ReleaseManifest.parse_version(current[1:]) for current in tags]
    return next((current for current in versions if current is not None), None)


def _base_manifest(base: str) -> ReleaseManifest | None:
    try:
        return ReleaseManifest.from_yaml(_git("show", f"{base}:{MANIFEST}"))
    except subprocess.CalledProcessError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description = "Checks deploy/release.yaml against what the pull request changes.")
    parser.add_argument("--base", required = True, help = "The branch the pull request merges into, e.g. origin/main")
    arguments = parser.parse_args()

    manifest = ReleaseManifest.load()
    changed = _git("diff", "--name-only", f"{arguments.base}...HEAD").split()
    rules = ReleaseRules(manifest, changed, _base_manifest(arguments.base), _released_version())
    violations = rules.violations()

    verdict = "a new release" if rules.declares_release else "no new release"
    lines = [f"Release {manifest.version} ({verdict}): infrastructure {manifest.infrastructure.value}, database {manifest.database.value}"]
    lines += [f"- {current}" for current in violations] or ["- follows the release rules"]
    print("\n".join(lines))
    write_summary("### Release\n\n" + "\n".join(lines))
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
