from enum import Enum


class RagSemanticScoringType(str, Enum):
    """Enumerates the ways the semantic chunker prices its choices from sentence
    embeddings: what each cut between two sentences costs and what each extension of a
    chunk by the next sentence costs. TEXT_TILING prices a cut by how deep the
    similarity of the sentences around it dips, and an extension by how much the
    sentence adds to the direction its chunk already has."""

    TEXT_TILING = "text_tiling"
