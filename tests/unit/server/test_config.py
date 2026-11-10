import pytest
from pydantic import ValidationError

from db import DEFAULT_SQLITE_PATH
from app.server.config import Config
from app.server.config_environment import ConfigEnvironment

PROD = {
    "VELA47_ENVIRONMENT": "prod",
    "VELA47_APP_SECRET_ID": "vela47/app",
    "VELA47_AWS_REGION": "eu-central-1",
    "VELA47_DATABASE_HOST": "vela47.abc.eu-central-1.rds.amazonaws.com",
    "VELA47_DATABASE_SECRET_ID": "rds!db-123"
}


def make_reader(secret = None, reads = None):
    def reader(secret_id, region):
        if reads is not None:
            reads.append((secret_id, region))
        return secret if secret is not None else {"token_secret": "t" * 32}
    return reader


class TestConfig:
    def test_with_nothing_set_it_is_dev_on_the_default_sqlite_file(self):
        config = Config.from_environment({})
        assert config.environment is ConfigEnvironment.DEV
        assert config.database.sqlite_path == DEFAULT_SQLITE_PATH

    def test_dev_takes_the_sqlite_file_from_the_environment(self):
        config = Config.from_environment({"VELA47_SQLITE_PATH": "/tmp/vela47.sqlite3"})
        assert str(config.database.sqlite_path) == "/tmp/vela47.sqlite3"

    def test_dev_reads_its_secrets_from_the_environment(self):
        config = Config.from_environment({
            "VELA47_TOKEN_SECRET": "s" * 32,
            "VELA47_ADMIN_USERNAME": "root",
            "VELA47_ADMIN_PASSWORD": "admin-password-long"
        })
        assert config.token_secret.get_secret_value() == "s" * 32
        assert config.admin_username == "root"
        assert config.admin_password.get_secret_value() == "admin-password-long"

    def test_dev_never_touches_secrets_manager(self):
        reads = []
        Config.from_environment({}, make_reader(reads = reads))
        assert reads == []

    def test_empty_variables_count_as_unset(self):
        config = Config.from_environment({"VELA47_TOKEN_SECRET": "", "VELA47_SQLITE_PATH": ""})
        assert config.token_secret is None and config.database.sqlite_path == DEFAULT_SQLITE_PATH

    def test_an_unknown_environment_is_refused(self):
        with pytest.raises(ValueError):
            Config.from_environment({"VELA47_ENVIRONMENT": "staging"})

    def test_prod_reads_the_application_secret_once_from_its_region(self):
        reads = []
        Config.from_environment(PROD, make_reader(reads = reads))
        assert reads == [("vela47/app", "eu-central-1")]

    def test_prod_takes_its_secrets_from_secrets_manager_not_the_environment(self):
        environment = dict(PROD, VELA47_TOKEN_SECRET = "e" * 32, VELA47_ADMIN_PASSWORD = "from-the-environment")
        config = Config.from_environment(environment, make_reader({
            "token_secret": "m" * 32, "admin_username": "root", "admin_password": "from-secrets-manager"
        }))
        assert config.token_secret.get_secret_value() == "m" * 32
        assert config.admin_password.get_secret_value() == "from-secrets-manager"

    def test_there_is_no_field_for_the_database_password_at_all(self):
        assert [current_name for current_name in Config.model_fields if "password" in current_name] == ["admin_password"]

    def test_prod_reads_the_database_settings_from_the_environment(self):
        environment = dict(PROD, VELA47_DATABASE_PORT = "6543", VELA47_DATABASE_NAME = "other", VELA47_DATABASE_SSL_MODE = "verify-full")
        database = Config.from_environment(environment, make_reader()).database
        assert database.host == "vela47.abc.eu-central-1.rds.amazonaws.com" and database.secret_id == "rds!db-123"
        assert database.port == 6543 and database.name == "other" and database.ssl_mode == "verify-full"

    def test_prod_falls_back_to_the_standard_aws_region_variable(self):
        environment = {current_key: current_value for current_key, current_value in PROD.items() if current_key != "VELA47_AWS_REGION"}
        reads = []
        Config.from_environment(dict(environment, AWS_REGION = "us-east-1"), make_reader(reads = reads))
        assert reads[0][1] == "us-east-1"

    def test_prod_without_an_application_secret_id_cannot_start(self):
        environment = {current_key: current_value for current_key, current_value in PROD.items() if current_key != "VELA47_APP_SECRET_ID"}
        with pytest.raises(ValueError):
            Config.from_environment(environment, make_reader())

    def test_prod_without_a_database_endpoint_cannot_start(self):
        environment = {current_key: current_value for current_key, current_value in PROD.items() if current_key != "VELA47_DATABASE_HOST"}
        with pytest.raises(ValidationError, match = "database.host"):
            Config.from_environment(environment, make_reader())

    def test_prod_without_a_database_secret_cannot_start(self):
        with pytest.raises(ValidationError, match = "database.secret_id"):
            Config.from_environment(dict(PROD, VELA47_DATABASE_SECRET_ID = ""), make_reader())

    def test_prod_whose_secret_lacks_a_token_secret_cannot_start(self):
        with pytest.raises(ValidationError):
            Config.from_environment(PROD, make_reader({"admin_username": "root"}))

    def test_document_limits_default_to_half_a_megabyte_and_two_megabytes(self):
        config = Config.from_environment({})
        assert config.knowledge_max_file_bytes == 512 * 1024 and config.knowledge_max_owner_bytes == 2 * 1024 * 1024

    def test_a_file_may_be_up_to_eight_megabytes_before_its_text_is_extracted(self):
        assert Config.from_environment({}).knowledge_max_upload_bytes == 8 * 1024 * 1024
        assert Config.from_environment({"VELA47_KNOWLEDGE_MAX_UPLOAD_BYTES": "1024"}).knowledge_max_upload_bytes == 1024

    def test_document_limits_come_from_the_environment_in_both_modes(self):
        config = Config.from_environment(dict(PROD, VELA47_KNOWLEDGE_MAX_OWNER_BYTES = "4096"), make_reader())
        assert config.knowledge_max_owner_bytes == 4096

    def test_secrets_never_show_in_a_repr(self):
        config = Config.from_environment({"VELA47_TOKEN_SECRET": "s" * 32, "VELA47_ADMIN_PASSWORD": "admin-password-long"})
        assert "s" * 32 not in repr(config) and "admin-password-long" not in repr(config)
