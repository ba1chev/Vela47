from app.intelligence.model import ModelConfig
from app.intelligence.model import ModelFoundation


def make_options(**fields):
    return ModelFoundation(ModelConfig(model_name = "qwen3:1.7b", **fields))._build_options()


class TestModelFoundationOptions:
    def test_think_never_travels_among_the_sampling_options(self):
        assert "think" not in make_options(think = True)
        assert "think" not in make_options(think = False)

    def test_a_context_window_becomes_num_ctx(self):
        assert make_options(context_window_tokens = 8192)["num_ctx"] == 8192

    def test_without_a_context_window_ollamas_default_is_left_alone(self):
        assert "num_ctx" not in make_options()
