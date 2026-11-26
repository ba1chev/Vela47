#!/usr/bin/env bash
# One-time setup of the AWS account for the pipeline, run by hand with administrator credentials in the AWS CLI:
#   deploy/bootstrap.sh          asks before every Terraform apply
#   deploy/bootstrap.sh --yes    applies without asking
# It is safe to run again: every step only changes what is missing or different.
#
#   1. the GitHub OpenID Connect provider, if the account has none
#   2. the role vela47-role: created if missing, its trust policy set to this repository (main and the dev, staging and
#      prod environments) and its sessions allowed to last two hours, as long as a deployment may take
#   3. shared/s3_state: the state bucket, applied with a local state that is then moved into the bucket
#   4. shared/iam: the permissions of vela47-role and the boundary of every role the pipeline creates
#   5. shared/artifacts and shared/ecr: the bucket of the releases and the image repositories
#
# What only GitHub can hold is printed at the end. See docs/open_id_connect.md and docs/deployment_order.md.
set -euo pipefail

REGION="eu-central-1"
ROLE_NAME="vela47-role"
STATE_BUCKET="vela47-terraform-state"
OIDC_HOST="token.actions.githubusercontent.com"
SUBJECT_PREFIX="repo:ba1chev@282053563/Vela47@1436127823"
SESSION_SECONDS=7200
SHARED="$(cd "$(dirname "$0")" && pwd)/terraform/environments/shared"

approve=""
[ "${1:-}" = "--yes" ] && approve="-input=false -auto-approve"

step() { printf '\n==> %s\n' "$1"; }

step "Checking the tools and the account"
command -v aws > /dev/null || { echo "The AWS CLI is not installed."; exit 1; }
command -v terraform > /dev/null || { echo "Terraform is not installed."; exit 1; }
account="$(aws sts get-caller-identity --query Account --output text)"
caller="$(aws sts get-caller-identity --query Arn --output text)"
echo "Account $account as $caller, region $REGION"
if [ -z "$approve" ]; then
  read -r -p "Set up this account for the Vela47 pipeline? [y/N] " answer
  [ "$answer" = "y" ] || [ "$answer" = "Y" ] || { echo "Nothing changed."; exit 0; }
fi
export AWS_REGION="$REGION" AWS_DEFAULT_REGION="$REGION"
export TF_PLUGIN_CACHE_DIR="${TF_PLUGIN_CACHE_DIR:-$HOME/.terraform.d/plugin-cache}"
mkdir -p "$TF_PLUGIN_CACHE_DIR"

step "GitHub OpenID Connect provider"
provider_arn="arn:aws:iam::$account:oidc-provider/$OIDC_HOST"
if aws iam get-open-id-connect-provider --open-id-connect-provider-arn "$provider_arn" > /dev/null 2>&1; then
  echo "Exists: $provider_arn"
else
  aws iam create-open-id-connect-provider --url "https://$OIDC_HOST" --client-id-list sts.amazonaws.com > /dev/null
  echo "Created: $provider_arn"
fi

step "Role $ROLE_NAME"
trust_policy="$(cat <<JSON
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Federated": "$provider_arn" },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "$OIDC_HOST:aud": "sts.amazonaws.com",
          "$OIDC_HOST:sub": [
            "$SUBJECT_PREFIX:ref:refs/heads/main",
            "$SUBJECT_PREFIX:environment:dev",
            "$SUBJECT_PREFIX:environment:staging",
            "$SUBJECT_PREFIX:environment:prod"
          ]
        }
      }
    }
  ]
}
JSON
)"
if aws iam get-role --role-name "$ROLE_NAME" > /dev/null 2>&1; then
  aws iam update-assume-role-policy --role-name "$ROLE_NAME" --policy-document "$trust_policy"
  echo "Trust policy set"
else
  aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document "$trust_policy" \
    --description "Assumed by the GitHub Actions workflows of Vela47 through OpenID Connect" > /dev/null
  echo "Created with its trust policy"
fi
aws iam update-role --role-name "$ROLE_NAME" --max-session-duration "$SESSION_SECONDS"
echo "Sessions may last $SESSION_SECONDS seconds"

step "shared/s3_state"
if aws s3api head-bucket --bucket "$STATE_BUCKET" > /dev/null 2>&1; then
  terraform -chdir="$SHARED/s3_state" init -input=false -migrate-state -force-copy
  terraform -chdir="$SHARED/s3_state" apply $approve
else
  printf 'terraform {\n  backend "local" {}\n}\n' > "$SHARED/s3_state/backend_override.tf"
  trap 'rm -f "$SHARED/s3_state/backend_override.tf"' EXIT
  terraform -chdir="$SHARED/s3_state" init -input=false -reconfigure
  terraform -chdir="$SHARED/s3_state" apply $approve
  rm -f "$SHARED/s3_state/backend_override.tf"
  trap - EXIT
  terraform -chdir="$SHARED/s3_state" init -input=false -migrate-state -force-copy
  rm -f "$SHARED/s3_state/terraform.tfstate" "$SHARED/s3_state/terraform.tfstate.backup"
  echo "The state of shared/s3_state is now in s3://$STATE_BUCKET/shared/s3_state/"
fi

for root in iam artifacts ecr; do
  step "shared/$root"
  terraform -chdir="$SHARED/$root" init -input=false
  terraform -chdir="$SHARED/$root" apply $approve
done

step "Done in AWS. Still to do in GitHub (Settings of the repository)"
cat <<TEXT
1. Secrets and variables → Actions → Variables: AWS_ROLE_ARN = arn:aws:iam::$account:role/$ROLE_NAME
2. Secrets and variables → Actions → Secrets: TAVILY_API_KEY = your Tavily key, without quotes
3. Environments: dev, staging and prod, each limited to the main branch; staging and prod with required reviewers
4. Branches: protect main, require pull requests and the CI checks
Then re-run the failed jobs of the last Delivery run.
TEXT
