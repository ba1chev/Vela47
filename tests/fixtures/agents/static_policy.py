from app.intelligence.agents import OperationPolicy


class StaticPolicy(OperationPolicy):
    """Resolves to a fixed list of layers handed over at construction, so a pipeline
    test chooses its own stages instead of depending on what a real policy builds."""

    def __init__(self, layers) -> None:
        self._layers = list(layers)

    def resolve(self, factory):
        return self._layers
