import pytest

from app.intelligence.loaders import LoaderPdf
from app.intelligence.loaders import LoaderDocx
from app.intelligence.loaders import LoaderHtml
from app.intelligence.loaders import LoaderText
from app.intelligence.loaders import LoaderType
from app.intelligence.loaders import LoadersFactory


class TestLoadersFactory:
    def test_every_type_builds_its_loader(self):
        factory = LoadersFactory()
        assert isinstance(factory.create(LoaderType.TEXT), LoaderText)
        assert isinstance(factory.create(LoaderType.HTML), LoaderHtml)
        assert isinstance(factory.create(LoaderType.PDF), LoaderPdf)
        assert isinstance(factory.create(LoaderType.DOCX), LoaderDocx)

    def test_each_loader_reports_its_type(self):
        assert all(LoadersFactory().create(current).loader_type is current for current in LoaderType)

    def test_an_unknown_type_is_refused(self):
        with pytest.raises(ValueError, match = "No loader class registered"):
            LoadersFactory().create("rtf")
