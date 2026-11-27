#!/usr/bin/env bash
# Destroys one root module of an AWS environment, and skips a root whose state holds nothing, so an environment that
# was never deployed or is half torn down can be torn down all the same. While it runs, the network interfaces Lambda
# leaves behind for the sandbox function are deleted as soon as AWS releases them: the security group of the function
# can only go once they are gone, which can take half an hour. A destroy that still times out is tried again.
#   teardown_root.sh <root module directory> <sandbox function name>
set -uo pipefail

directory="$1"
function_name="$2"

terraform -chdir="$directory" init -input=false -lockfile=readonly > /dev/null || exit 1
if [ -z "$(terraform -chdir="$directory" state list 2> /dev/null)" ]; then
  echo "Nothing to destroy in $directory"
  exit 0
fi

release_interfaces() {
  while true; do
    for interface in $(aws ec2 describe-network-interfaces \
      --filters "Name=description,Values=AWS Lambda VPC ENI-$function_name" "Name=status,Values=available" \
      --query 'NetworkInterfaces[].NetworkInterfaceId' --output text); do
      aws ec2 delete-network-interface --network-interface-id "$interface" && echo "Deleted $interface, released by Lambda"
    done
    sleep 30
  done
}
release_interfaces &
cleaner=$!
trap 'kill "$cleaner" 2> /dev/null' EXIT

for attempt in 1 2 3; do
  terraform -chdir="$directory" destroy -auto-approve -input=false -lock-timeout=5m && exit 0
  echo "Destroy attempt $attempt of $directory failed, trying again"
done
exit 1
