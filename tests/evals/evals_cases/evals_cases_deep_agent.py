from app.intelligence.agents import OperationSubagentType
from tests.evals.evals_cases.evals_case_deep_agent import EvalsCaseDeepAgent


EVALS_CASES_DEEP_AGENT: list[EvalsCaseDeepAgent] = [
    EvalsCaseDeepAgent(
        id = "hackathon",
        goal = "make me a plan about the coming hackaton at amunset this mounth",
        allowed_types = frozenset({OperationSubagentType.RESEARCH}),
        required_types = (OperationSubagentType.RESEARCH,),
        max_steps = 3,
        names_pattern = r"amunset|amusnet"
    ),
    EvalsCaseDeepAgent(
        id = "is_prime",
        goal = "Write a Python function is_prime(n) in primes.py and tests for it",
        allowed_types = frozenset({OperationSubagentType.CODE, OperationSubagentType.TEST}),
        required_types = (OperationSubagentType.CODE, OperationSubagentType.TEST),
        max_steps = 3,
        names_pattern = r"is_prime|primes\.py",
        hidden_test_file = "primes.py",
        hidden_test_code = (
            "from primes import is_prime\n\n"
            "def test_hidden():\n"
            "    assert [n for n in range(-3, 30) if is_prime(n)] == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]\n"
            "    assert is_prime(97) and not is_prime(91) and not is_prime(1) and not is_prime(0)\n"
        )
    ),
    EvalsCaseDeepAgent(
        id = "python_version",
        goal = "What is the latest stable version of Python and what are its main new features?",
        allowed_types = frozenset({OperationSubagentType.RESEARCH}),
        required_types = (OperationSubagentType.RESEARCH,),
        max_steps = 2,
        names_pattern = r"python"
    ),
    EvalsCaseDeepAgent(
        id = "slugify",
        goal = "Create a slugify(text) function in text_utils.py that lowercases the text, trims it and "
            "replaces runs of spaces with single dashes, then review it for edge cases",
        allowed_types = frozenset({OperationSubagentType.CODE, OperationSubagentType.REVIEW}),
        required_types = (OperationSubagentType.CODE, OperationSubagentType.REVIEW),
        max_steps = 3,
        names_pattern = r"slugify|text_utils",
        hidden_test_file = "text_utils.py",
        hidden_test_code = (
            "from text_utils import slugify\n\n"
            "def test_hidden():\n"
            "    assert slugify('  Hello   World  ') == 'hello-world'\n"
            "    assert slugify('Python') == 'python'\n"
        )
    ),
    EvalsCaseDeepAgent(
        id = "question_in_bulgarian",
        goal = "Какво е RAG (retrieval-augmented generation) и как работи? Отговори накратко.",
        allowed_types = frozenset({OperationSubagentType.RESEARCH}),
        required_types = (OperationSubagentType.RESEARCH,),
        max_steps = 2,
        names_pattern = r"rag|retrieval"
    ),
]
