RAG_NO_SOURCES_PROMPT = """A user asked: «{question}»
A search of their own documents found nothing that answers it.

First name the language that question is written in. Then write the reply in that language: one or two sentences telling the user their documents do not cover it and that they can upload a document that does. Do not answer the question, and do not mention the language in the reply.

Reply with JSON only: {{"language": "...", "reply": "..."}}"""
