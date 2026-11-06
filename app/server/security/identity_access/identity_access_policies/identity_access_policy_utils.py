import re
from typing import Optional

PATTERN_TOKEN = re.compile(r"\$\{([a-z_.]+)\}|\*|\?")


def matches_pattern(pattern: str, value: str,
    variables: Optional[dict[str, str]] = None, case_sensitive: bool = True) -> bool:
    expression: list[str] = []
    position = 0

    for current_token in PATTERN_TOKEN.finditer(pattern):
        expression.append(re.escape(pattern[position:current_token.start()]))

        if current_token.group(0) == "*":
            expression.append(".*")
        elif current_token.group(0) == "?":
            expression.append(".")
        else:
            resolved = (variables or {}).get(current_token.group(1))
            if resolved is None:
                return False
            expression.append(re.escape(resolved))

        position = current_token.end()

    expression.append(re.escape(pattern[position:]))
    flags = re.DOTALL if case_sensitive else re.DOTALL | re.IGNORECASE
    return re.fullmatch("".join(expression), value, flags) is not None
