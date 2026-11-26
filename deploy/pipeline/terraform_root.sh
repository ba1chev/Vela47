#!/usr/bin/env bash
# Plans one root module of an AWS environment from an extracted release bundle and checks the plan against the
# release (PlanGuard). With "apply" it then applies exactly the plan it checked. Run from the bundle's directory.
#   terraform_root.sh plan|apply <environment> <root> <release.yaml>
# Exit codes: 0 done, 3 Terraform failed, 4 the plan does more than the release declares.
# Whether the root had changes is written to $RUNNER_TEMP/<root name>.changes (true or false).
set -uo pipefail

mode="$1"
environment="$2"
root="$3"
release="$4"
directory="deploy/terraform/environments/$environment/$root"
name="${root%%/*}"
log="$RUNNER_TEMP/$name.log"

if ! terraform -chdir="$directory" init -input=false -lockfile=readonly > "$log" 2>&1; then
  tail -30 "$log"
  exit 3
fi

terraform -chdir="$directory" plan -input=false -lock-timeout=5m -detailed-exitcode -out=tfplan > "$log" 2>&1
case $? in
  0) echo false > "$RUNNER_TEMP/$name.changes" ;;
  2) echo true > "$RUNNER_TEMP/$name.changes" ;;
  *) tail -30 "$log"; exit 3 ;;
esac

terraform -chdir="$directory" show -json tfplan > "$RUNNER_TEMP/$name.plan.json" || exit 3
python -m deploy.pipeline.commands.guard_plan --plan "$RUNNER_TEMP/$name.plan.json" --root "$name" --release "$release"
guarded=$?
rm -f "$RUNNER_TEMP/$name.plan.json"
[ "$guarded" -eq 0 ] || exit 4

if [ "$mode" = "apply" ] && [ "$(cat "$RUNNER_TEMP/$name.changes")" = "true" ]; then
  terraform -chdir="$directory" apply -input=false -lock-timeout=5m tfplan || exit 3
fi
rm -f "$directory/tfplan"
exit 0
