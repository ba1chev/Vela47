import os

EVALS_RUNS = int(os.environ.get("VELA47_EVALS_RUNS", "3"))
EVALS_JUDGE_MODEL = os.environ.get("VELA47_EVALS_JUDGE_MODEL", "qwen3:14b")
