from pydantic import BaseModel, Field


class RagNoSourcesReply(BaseModel):
    """What the generation model writes when no passage survived reranking: the
    language of the user's question, then the reply in that language. Naming the
    language first is the point. Told only to answer 'in the language of the
    question', qwen3:1.7b answered short Bulgarian questions in English nearly every
    time; made to write the language down before the reply, it wrote every reply in
    that language. Doubles as the schema that constrains the model's decoding."""

    language: str = Field(
        description = "The language the user's question is written in, named before the reply "
            "is written so the reply follows it."
    )
    reply: str = Field(
        description = "One or two sentences, in that language, telling the user their documents "
            "do not cover the question and that they can upload one that does."
    )
