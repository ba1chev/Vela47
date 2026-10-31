import pytest

from app.intelligence.agents import OperationType
from tests.fixtures.model.fake_model import FakeModel
from app.intelligence.agents import OperationLayersFactory
from app.intelligence.agents import OPERATION_LAYERS_REGISTRY


class TestOperationLayersFactory:
    def test_every_type_is_registered(self):
        for operation_type in OperationType:
            assert operation_type in OPERATION_LAYERS_REGISTRY

    def test_it_builds_the_layer_for_a_type(self):
        layer = OperationLayersFactory().create(OperationType.DECOMPOSITION)
        assert layer.operation_type is OperationType.DECOMPOSITION

    def test_keyword_arguments_are_forwarded(self):
        model = FakeModel()
        layer = OperationLayersFactory().create(OperationType.MERGING, model = model)
        assert layer._model is model

    def test_an_unknown_type_is_refused_with_the_known_ones(self):
        with pytest.raises(ValueError, match = "No layer class registered"):
            OperationLayersFactory().create("not-a-type")
