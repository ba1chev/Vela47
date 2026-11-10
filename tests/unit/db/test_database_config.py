import pytest
import pathlib
from pydantic import ValidationError

from db import DatabaseConfig
from db import DEFAULT_SQLITE_PATH


class TestDatabaseConfig:
    def test_by_default_it_is_the_sqlite_file_in_the_db_directory(self):
        assert DatabaseConfig().sqlite_path == DEFAULT_SQLITE_PATH
        assert DEFAULT_SQLITE_PATH.parent.name == "db"
        assert DEFAULT_SQLITE_PATH.parent.parent == pathlib.Path(__file__).resolve().parents[3]

    def test_postgres_defaults_to_an_encrypted_connection_to_vela47_on_5432(self):
        config = DatabaseConfig()
        assert (config.port, config.name, config.ssl_mode) == (5432, "vela47", "require")
        assert config.host is None and config.secret_id is None

    def test_a_port_given_as_text_is_read_as_a_number(self):
        assert DatabaseConfig(port = "6543").port == 6543

    @pytest.mark.parametrize("field, value", [("port", 0), ("name", "")])
    def test_an_impossible_setting_is_refused(self, field, value):
        with pytest.raises(ValidationError):
            DatabaseConfig(**{field: value})

    def test_there_is_no_field_for_a_password(self):
        assert [current_name for current_name in DatabaseConfig.model_fields if "password" in current_name] == []

    def test_it_cannot_be_changed_once_built(self):
        with pytest.raises(ValidationError):
            DatabaseConfig().host = "elsewhere"
