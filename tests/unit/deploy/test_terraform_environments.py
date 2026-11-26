import re
import pathlib

TERRAFORM = pathlib.Path(__file__).resolve().parents[3] / "deploy" / "terraform"
ENVIRONMENTS = TERRAFORM / "environments"
MODULES = TERRAFORM / "modules"
AWS_ENVIRONMENTS = ("dev", "staging", "prod")
ROOTS = ("vpc/eu-central-1", "database", "app")
IDENTITIES = {
    "staging": {"vela47-staging.y47.sevc.link": "<domain>", "10.20.": "<cidr>.", "staging": "<environment>"},
    "prod": {"vela47.y47.sevc.link": "<domain>", "10.30.": "<cidr>.", "prod": "<environment>"},
}


def terraform_files(directory):
    return {current.name: current.read_text() for current in sorted(directory.glob("*.tf"))}


def default_of(text, variable):
    found = re.search(rf'variable "{variable}" \{{.*?default\s*=\s*([^\n]+)', text, re.DOTALL)
    return found.group(1).strip().strip('"') if found else None


def normalized(environment, text):
    for current, replacement in IDENTITIES[environment].items():
        text = text.replace(current, replacement)
    return text


class TestTerraformEnvironments:
    def test_every_aws_environment_has_the_same_roots_and_files(self):
        for current_environment in AWS_ENVIRONMENTS:
            for current_root in ROOTS:
                assert set(terraform_files(ENVIRONMENTS / current_environment / current_root)) == {
                    "main.tf", "outputs.tf", "state.tf", "variables.tf", "versions.tf"
                }

    def test_staging_differs_from_prod_only_in_its_name_domain_and_addresses(self):
        for current_root in ROOTS:
            staging = terraform_files(ENVIRONMENTS / "staging" / current_root)
            prod = terraform_files(ENVIRONMENTS / "prod" / current_root)
            assert {name: normalized("staging", text) for name, text in staging.items()} == {
                name: normalized("prod", text) for name, text in prod.items()
            }

    def test_every_root_keeps_its_state_under_its_own_path(self):
        for current in ENVIRONMENTS.rglob("state.tf"):
            if ".terraform" in current.parts or "local" in current.parts:
                continue
            key = re.search(r'key\s*=\s*"([^"]+)"', current.read_text()).group(1)
            assert key == f"{current.parent.relative_to(ENVIRONMENTS)}/terraform.tfstate"

    def test_dev_is_cheap_and_staging_and_prod_are_safe(self):
        def value(environment, root, variable):
            return default_of((ENVIRONMENTS / environment / root / "variables.tf").read_text(), variable)

        assert value("dev", "vpc/eu-central-1", "nat_type") == "instance"
        assert value("dev", "app", "deployment_strategy") == "ROLLING" and value("dev", "app", "instance_min_count") == "0"
        assert value("dev", "database", "multi_az") == "false"
        for current in ("staging", "prod"):
            assert value(current, "vpc/eu-central-1", "nat_type") == "gateway"
            assert value(current, "app", "deployment_strategy") == "CANARY"
            assert value(current, "database", "multi_az") == "true" and value(current, "database", "deletion_protection") == "true"
            assert value(current, "database", "skip_final_snapshot") == "false"

    def test_only_dev_keeps_office_hours(self):
        assert 'module "schedule"' in (ENVIRONMENTS / "dev" / "app" / "main.tf").read_text()
        assert all('module "schedule"' not in (ENVIRONMENTS / current / "app" / "main.tf").read_text() for current in ("staging", "prod"))

    def test_a_release_is_always_named_never_defaulted(self):
        for current_environment in AWS_ENVIRONMENTS:
            variables = (ENVIRONMENTS / current_environment / "app" / "variables.tf").read_text()
            block = re.search(r'variable "release_version" \{(.*?)\n\}', variables, re.DOTALL).group(1)
            assert "default" not in block

    def test_every_role_the_pipeline_creates_carries_the_boundary(self):
        for current in MODULES.rglob("*.tf"):
            for role in re.findall(r'resource "aws_iam_role" "[^"]+" \{(.*?)\n\}', current.read_text(), re.DOTALL):
                assert "permissions_boundary = var.permissions_boundary_arn" in re.sub(r"\s+", " ", role), current

    def test_the_pipeline_may_launch_every_instance_type_the_environments_use(self):
        allowed = re.findall(r'"(t4g\.\w+)"', default_of((ENVIRONMENTS / "shared" / "iam" / "variables.tf").read_text(), "instance_types"))
        used = {default_of((ENVIRONMENTS / current / "app" / "variables.tf").read_text(), "instance_type") for current in AWS_ENVIRONMENTS}
        used.add(default_of((MODULES / "vpc" / "variables.tf").read_text(), "nat_instance_type"))
        assert used <= set(allowed)
