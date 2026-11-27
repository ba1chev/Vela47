from deploy.pipeline import ReleaseCatalog
from tests.fixtures.deploy.in_memory_s3_client import InMemoryS3Client


def make_catalog(*versions):
    s3 = InMemoryS3Client()
    for current in versions:
        s3.put_object("vela47-artifacts", f"releases/{current}/release.yaml", b"", "text/yaml")
        s3.put_object("vela47-artifacts", f"releases/{current}/deploy.tar.gz", b"", "application/gzip")
    return ReleaseCatalog(s3, "vela47-artifacts")


class TestReleaseCatalog:
    def test_versions_are_ordered_as_versions_not_as_text(self):
        assert make_catalog("1.10.0", "2.0.0", "1.9.3").versions() == ["1.9.3", "1.10.0", "2.0.0"]

    def test_the_newest_release_is_the_highest_version(self):
        assert make_catalog("1.0.3", "2.0.0", "1.0.2").newest() == "2.0.0"

    def test_an_empty_bucket_has_no_release(self):
        assert make_catalog().newest() is None

    def test_a_prefix_that_is_not_a_version_is_ignored(self):
        assert make_catalog("2.0.0", "latest").versions() == ["2.0.0"]
