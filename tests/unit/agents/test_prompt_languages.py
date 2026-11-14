import re

from app.intelligence import agents

LANGUAGE_WORDS = re.compile(r"language|bulgarian|english|[а-яА-Я]", re.IGNORECASE)


def every_prompt():
    for current_name in agents.__all__:
        current = getattr(agents, current_name)
        if current_name.endswith(("_PROMPT", "_TEMPLATE")):
            yield current_name, current
        elif current_name.endswith(("_TEMPLATES", "_CAPABILITIES")):
            for current_type, current_text in current.items():
                yield f"{current_name}[{current_type.name}]", current_text


class TestPromptLanguages:
    def test_there_are_prompts_to_check(self):
        assert len(list(every_prompt())) >= 15

    def test_no_prompt_talks_about_languages(self):
        """A small model told to mind languages mixes them; every prompt stays in one
        language and says nothing about which one the answer should be in."""
        offending = {current_name: LANGUAGE_WORDS.findall(current_text) for current_name, current_text in every_prompt()}
        assert {current_name: found for current_name, found in offending.items() if found} == {}
