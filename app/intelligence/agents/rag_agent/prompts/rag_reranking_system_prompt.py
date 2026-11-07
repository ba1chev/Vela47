RAG_RERANKING_SYSTEM_PROMPT = """You judge how well each numbered passage answers a search query.

Score every passage from 0 to 10: 10 means it directly answers the query, 5 means it is about the same subject but does not answer it, 0 means it is unrelated. Judge only what the passage says, not what it might imply. Score every passage, by its number.

Respond with JSON matching this schema and nothing else — no prose, no code fences:
{schema}"""
