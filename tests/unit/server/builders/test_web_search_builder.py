import re
import pathlib

from app.server.config import Config
from app.intelligence.web import WebFetcher
from app.intelligence.web import WebSearchType
from app.intelligence.web import WebSearchTavily
from app.server.builders import WEB_SEARCH_TYPES
from app.server.builders import build_web_search
from app.intelligence.web import WebSearchDuckDuckGo
from app.server.config_environment import ConfigEnvironment

TERRAFORM = pathlib.Path(__file__).resolve().parents[4] / "deploy" / "terraform"
PROD_APP = TERRAFORM / "environments" / "prod" / "app"
APP_MODULE = TERRAFORM / "modules" / "app"


def prod_config(tavily_api_key = None):
    return Config(
        environment = ConfigEnvironment.PROD,
        database = {"host": "db", "secret_id": "rds!db"},
        aws_region = "eu-central-1",
        token_secret = "t" * 32,
        tavily_api_key = tavily_api_key
    )


class TestWebSearchBuilder:
    def test_every_environment_has_a_search_engine(self):
        assert set(WEB_SEARCH_TYPES) == set(ConfigEnvironment)

    def test_development_searches_through_duckduckgo(self):
        assert WEB_SEARCH_TYPES[ConfigEnvironment.DEV] is WebSearchType.DUCKDUCKGO
        assert isinstance(build_web_search(Config(), WebFetcher()), WebSearchDuckDuckGo)

    def test_production_with_a_key_searches_through_tavily(self):
        assert isinstance(build_web_search(prod_config("tvly-key"), WebFetcher()), WebSearchTavily)

    def test_production_without_a_key_falls_back_to_duckduckgo(self):
        assert isinstance(build_web_search(prod_config(), WebFetcher()), WebSearchDuckDuckGo)

    def test_the_application_secret_terraform_writes_holds_the_key_the_server_reads(self):
        secrets = (APP_MODULE / "secrets.tf").read_text()
        secret = re.search(r'resource "aws_secretsmanager_secret_version" "app" \{.*?jsonencode\(\{(.*?)\}\)', secrets, re.DOTALL)
        assert re.search(r"^\s*tavily_api_key\s*=\s*var\.tavily_api_key\s*$", secret.group(1), re.MULTILINE)

    def test_the_key_is_a_sensitive_variable_that_may_stay_empty(self):
        variables = (PROD_APP / "variables.tf").read_text()
        block = re.search(r'variable "tavily_api_key" \{(.*?)\n\}', variables, re.DOTALL).group(1)
        assert re.search(r"sensitive\s*=\s*true", block) and re.search(r'default\s*=\s*""', block)
