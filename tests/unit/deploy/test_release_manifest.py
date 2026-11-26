import pytest
from pydantic import ValidationError

from deploy.pipeline import DatabaseChange
from deploy.pipeline import ReleaseManifest
from deploy.pipeline import InfrastructureChange


def make_manifest(version = "1.2.3", infrastructure = "none", database = "none"):
    return ReleaseManifest(version = version, infrastructure = infrastructure, database = database, summary = "s")


class TestReleaseManifest:
    def test_the_repository_declares_a_valid_release(self):
        manifest = ReleaseManifest.load()
        assert manifest.version_key >= (1, 0, 0) and manifest.summary

    def test_a_version_is_semantic(self):
        assert make_manifest("10.0.7").version_key == (10, 0, 7)
        for current in ("1.2", "v1.2.3", "01.2.3", "1.2.3-rc1"):
            with pytest.raises(ValidationError):
                make_manifest(current)

    def test_only_declared_kinds_of_change_are_accepted(self):
        with pytest.raises(ValidationError):
            make_manifest(infrastructure = "huge")
        assert make_manifest(database = "expand").database is DatabaseChange.EXPAND

    def test_a_breaking_infrastructure_change_or_a_contract_migration_is_breaking(self):
        assert make_manifest(infrastructure = "breaking").breaking
        assert make_manifest(database = "contract").breaking
        assert not make_manifest(infrastructure = "additive", database = "expand").breaking

    def test_it_reads_the_yaml_the_repository_keeps(self):
        manifest = ReleaseManifest.from_yaml("version: 2.0.0\ninfrastructure: additive\ndatabase: none\nsummary: s\n")
        assert manifest.infrastructure is InfrastructureChange.ADDITIVE

    def test_a_tag_that_is_not_a_version_parses_to_nothing(self):
        assert ReleaseManifest.parse_version("latest") is None and ReleaseManifest.parse_version("3.1.4") == (3, 1, 4)
