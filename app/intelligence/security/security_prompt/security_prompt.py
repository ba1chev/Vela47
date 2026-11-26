import re
import unicodedata
from abc import abstractmethod

from app.intelligence.security import SecurityType
from app.intelligence.security import SecurityBase
from app.intelligence.security import SecurityPromptType
from app.intelligence.security import SecurityPromptVerdict


class SecurityPrompt(SecurityBase):
    """Abstract base of the prompt detectors. Each one names its threat and the signatures
    it looks for, from the shared ones held here and its own; inspect() is shared, so all
    three read a text the same way.

    A text is first made to read as a model reads it: characters a person cannot see are
    dropped, Unicode tag characters (invisible ASCII a model still reads) are decoded in
    place and look-alike forms such as full-width letters are folded by NFKC, so no
    instruction hides from a signature while a model would still follow it. Hidden tag
    text is a finding of its own, except the tags that spell a flag emoji. Every
    signature is bounded, so a long text costs linear time."""

    EXCERPT_CHARS = 160
    FLAG_EMOJI = "\U0001F3F4"
    TAG_CANCEL = "\U000E007F"
    TAG_CHARACTERS = re.compile(r"[\U000E0000-\U000E007F]+")
    INVISIBLE_CHARACTERS = re.compile(r"[​-‏‪-‮⁠-⁤⁦-⁩﻿]")
    OVERRIDE_INSTRUCTIONS = re.compile(
        r"\b(?:ignore|disregard|forget|override)\b[^.\n]{0,30}?"
        r"\b(?:previous|prior|above|earlier|preceding|all|any|your|original|system)\b[^.\n]{0,30}?"
        r"\b(?:instructions?|prompts?|rules|directives?|directions|guidelines)\b"
        r"|\b(?:ignore|disregard|forget)\s+(?:everything|all)\s+"
        r"(?:above|before|previous(?:ly)?|prior|you\s+(?:were|have\s+been)\s+told)\b",
        re.IGNORECASE
    )
    SYSTEM_IMPERSONATION = re.compile(
        r"\b(?:new|updated|revised|real|actual|true|hidden|secret|developer)\s+system\s+"
        r"(?:instructions?|prompts?|messages?|directives?)\b"
        r"|\bsystem\s+(?:override|instructions?)\s*:"
        r"|^[ \t>#*\[(<]*system[\])>* \t]*:?[ \t]*(?:you\b|ignore\b|from\s+now\b)",
        re.IGNORECASE | re.MULTILINE
    )
    PROMPT_EXTRACTION = re.compile(
        r"\b(?:reveal|print|show|repeat|output|display|leak|disclose|tell\s+me|give\s+me|write\s+out|dump|share)\b"
        r"[^.\n]{0,30}?\byour\s+(?:system|initial|hidden|original|full|secret|internal)\s+"
        r"(?:prompt|instructions?|message|rules)\b"
        r"|\brepeat\b[^.\n]{0,20}?\b(?:words|text|everything)\s+(?:above|before\s+this)\b"
        r"|\bwhat\s+(?:is|are|was|were)\s+your\s+"
        r"(?:system\s+prompt|(?:initial|original|hidden|secret)\s+(?:instructions|prompt))\b",
        re.IGNORECASE
    )
    ROLE_TOKENS = re.compile(
        r"<\|(?:im_start|im_end|im_sep|system|user|assistant|endoftext|eot_id|start_header_id|end_header_id"
        r"|begin_of_text)\|>|\[/?INST\]|<</?SYS>>|</?tool_call>|</?function_call>|</?tool_response>"
    )
    ADDRESS_TO_AI = re.compile(
        r"(?:\battention(?:\s+(?:to|for))?|\b(?:note|message|instructions?|reminder)\s+(?:to|for))\s+"
        r"(?:the\s+|any\s+|all\s+)?(?:ai(?:\s+(?:assistants?|agents?|models?))?|llms?|language\s+models?|chatbots?)\b"
        r"|\b(?:if|when)\s+you\s+are\s+(?:an?\s+)?(?:ai|llm|language\s+model|chatbot)\b"
        r"|\b(?:dear|hey|hello|hi)\s+(?:ai|llm|chatgpt|gpt|gemini|qwen|chatbot)\b"
        r"|\b(?:ai|llm|language\s+model|chatbot)s?\b[^.\n]{0,20}?"
        r"\b(?:reading|processing|summari[sz]ing|that\s+reads)\s+this\b",
        re.IGNORECASE
    )
    PIPELINE_MARKERS = re.compile(
        r"Checked by the system:|For context, the user's request was|The user's request:"
        r"|Report \((?:success|error)\):|Step \d+ \((?:RESEARCH|CODE|TEST|REVIEW)\):"
        r"|The system ran the tests after this step|The system carried \d+ message"
        r"|You have no turns left|You have not used any of your tools yet"
        r"|worker checking the code you wrote sends you this|The (?:RESEARCH|CODE|TEST|REVIEW) worker answered:"
        r"|^(?:SOURCES|PASSAGES):[ \t]*$|^(?:QUESTION|LATEST MESSAGE|STANDALONE QUERY):"
        r"|SAME QUERY, WITH ITS REFERENCES RESOLVED:",
        re.MULTILINE
    )
    EXFILTRATION_IMAGE = re.compile(
        r"!\[[^\]\n]{0,200}\]\(\s*<?https?://[^\s)?#]{1,200}[?#][^\s)]{0,300}?"
        r"(?:\{[^}\n)]{1,60}\}|\[[^\]\n)]{1,60}\]|<[^>\n)]{1,60}>|\$\{?[A-Za-z_]{1,60}\}?|%s)",
        re.IGNORECASE
    )

    @property
    def security_type(self) -> SecurityType:
        return SecurityType.PROMPT

    @property
    @abstractmethod
    def prompt_type(self) -> SecurityPromptType:
        raise NotImplementedError("Must be implemented")

    @property
    @abstractmethod
    def signatures(self) -> dict[str, re.Pattern]:
        raise NotImplementedError("Must be implemented")

    def _decoded(self, tags: str) -> str:
        return "".join(
            chr(ord(current) - 0xE0000) for current in tags if "\U000E0020" <= current <= "\U000E007E"
        )

    def _hidden(self, text: str) -> str:
        return " ".join(
            self._decoded(current.group())
            for current in self.TAG_CHARACTERS.finditer(text)
            if not (
                text[current.start() - 1:current.start()] == self.FLAG_EMOJI
                and current.group().endswith(self.TAG_CANCEL)
            )
        ).strip()

    def _readable(self, text: str) -> str:
        revealed = self.TAG_CHARACTERS.sub(lambda current: self._decoded(current.group()), text)
        return unicodedata.normalize("NFKC", self.INVISIBLE_CHARACTERS.sub("", revealed))

    def _excerpt(self, text: str) -> str:
        flattened = " ".join(text.split())
        if len(flattened) <= self.EXCERPT_CHARS:
            return flattened
        return flattened[:self.EXCERPT_CHARS - 1].rstrip() + "…"

    def inspect(self, text: str) -> SecurityPromptVerdict:
        matches: dict[str, str] = {}
        hidden = self._hidden(text)
        if hidden:
            matches["hidden_text"] = self._excerpt(hidden)

        readable = self._readable(text)
        for current_name, current_signature in self.signatures.items():
            found = current_signature.search(readable)
            if found is not None:
                matches[current_name] = self._excerpt(found.group())
        return SecurityPromptVerdict(prompt_type = self.prompt_type, matches = matches)
