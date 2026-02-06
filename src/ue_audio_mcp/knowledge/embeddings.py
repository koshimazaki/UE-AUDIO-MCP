"""TF-IDF + cosine similarity search engine for game audio knowledge entries.

Implements a lightweight semantic search over ~400 knowledge entries (MetaSounds
nodes, WAAPI functions, Wwise types, audio patterns) using only numpy.

Approach:
  1. Tokenize each document (name + description + tags) into lowercase terms
  2. Remove common English stop words
  3. Build a vocabulary mapping term -> column index
  4. Compute TF-IDF vectors:
     - TF  = term_count / max_term_count_in_doc  (augmented frequency, avoids length bias)
     - IDF = log(N / (1 + df))  where N = total docs, df = docs containing term
  5. L2-normalize each document vector
  6. At query time, build the same TF-IDF vector using stored IDF, normalize, then
     compute cosine similarity via dot product (both vectors are unit length).

This avoids any dependency on scikit-learn or sentence-transformers while providing
good retrieval quality for short technical descriptions with strong keyword signals.
"""

from __future__ import annotations

import math
import re

import numpy as np


# ===================================================================
# Stop words -- common English words that add noise to TF-IDF
# ===================================================================

STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "the", "is", "in", "of", "to", "for", "and", "or",
    "with", "on", "by", "at", "as", "it", "this", "that", "from",
    "are", "be", "was", "were", "has", "have", "been", "not", "but",
    "if", "can", "do", "will", "all", "each", "they", "its", "any",
    "more", "also", "no", "so", "when", "out", "up", "about",
})


# ===================================================================
# Tokenizer
# ===================================================================

_SPLIT_RE = re.compile(r"[^a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    """Split text into lowercase alphanumeric tokens, removing stop words."""
    tokens = _SPLIT_RE.split(text.lower())
    return [t for t in tokens if t and t not in STOP_WORDS]


# ===================================================================
# EmbeddingIndex
# ===================================================================

class EmbeddingIndex:
    """TF-IDF vector index for fast cosine similarity search.

    Parameters
    ----------
    entries : list[dict]
        Each entry must have ``"name"`` (str) and ``"text"`` (str) keys.
        The ``text`` field is a pre-combined string of name, description,
        and tags used for building the TF-IDF representation.
    """

    def __init__(self, entries: list[dict]) -> None:
        if not entries:
            raise ValueError("Cannot build index from empty entry list")

        self._names: list[str] = [e["name"] for e in entries]
        docs_tokens: list[list[str]] = [_tokenize(e["text"]) for e in entries]
        n_docs = len(docs_tokens)

        # --- Build vocabulary and document frequency ---
        df: dict[str, int] = {}  # term -> number of docs containing it
        for tokens in docs_tokens:
            for term in set(tokens):
                df[term] = df.get(term, 0) + 1

        # Sort vocabulary for deterministic column ordering
        self._vocab: dict[str, int] = {
            term: idx for idx, term in enumerate(sorted(df.keys()))
        }
        n_terms = len(self._vocab)

        # --- Compute IDF ---
        self._idf = np.zeros(n_terms, dtype=np.float64)
        for term, idx in self._vocab.items():
            self._idf[idx] = math.log(n_docs / (1 + df[term]))

        # --- Build TF-IDF matrix (n_docs x n_terms) ---
        matrix = np.zeros((n_docs, n_terms), dtype=np.float64)
        for doc_i, tokens in enumerate(docs_tokens):
            if not tokens:
                continue
            # Count term frequencies
            counts: dict[str, int] = {}
            for t in tokens:
                counts[t] = counts.get(t, 0) + 1
            max_count = max(counts.values())
            # Augmented TF * IDF
            for term, count in counts.items():
                col = self._vocab.get(term)
                if col is not None:
                    tf = count / max_count
                    matrix[doc_i, col] = tf * self._idf[col]

        # --- L2-normalize each row ---
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        # Avoid division by zero for empty docs
        norms = np.where(norms == 0, 1.0, norms)
        self._matrix = matrix / norms

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """Search the index and return the top-k (name, score) pairs.

        Parameters
        ----------
        query : str
            Natural language query string.
        top_k : int
            Number of results to return (default 10).

        Returns
        -------
        list[tuple[str, float]]
            List of (entry_name, cosine_similarity_score) sorted descending.
        """
        tokens = _tokenize(query)
        if not tokens:
            return []

        # Build query TF-IDF vector using stored IDF
        q_vec = np.zeros(len(self._vocab), dtype=np.float64)
        counts: dict[str, int] = {}
        for t in tokens:
            counts[t] = counts.get(t, 0) + 1
        max_count = max(counts.values())

        for term, count in counts.items():
            col = self._vocab.get(term)
            if col is not None:
                tf = count / max_count
                q_vec[col] = tf * self._idf[col]

        # L2-normalize
        norm = np.linalg.norm(q_vec)
        if norm == 0:
            return []
        q_vec /= norm

        # Cosine similarity = dot product (both unit vectors)
        scores = self._matrix @ q_vec

        # Get top-k indices
        if top_k >= len(scores):
            top_indices = np.argsort(scores)[::-1]
        else:
            # Use argpartition for efficiency on large arrays
            partitioned = np.argpartition(scores, -top_k)[-top_k:]
            top_indices = partitioned[np.argsort(scores[partitioned])[::-1]]

        return [
            (self._names[i], float(scores[i]))
            for i in top_indices
            if scores[i] > 0.0
        ]

    def save(self, path: str) -> None:
        """Save the index to a .npz file.

        Stores the TF-IDF matrix, IDF vector, vocabulary, and entry names.
        """
        vocab_terms = sorted(self._vocab.keys(), key=lambda t: self._vocab[t])
        np.savez_compressed(
            path,
            matrix=self._matrix,
            idf=self._idf,
            vocab_terms=np.array(vocab_terms, dtype=object),
            names=np.array(self._names, dtype=object),
        )

    @classmethod
    def load(cls, path: str) -> EmbeddingIndex:
        """Load a previously saved index from a .npz file.

        Parameters
        ----------
        path : str
            Path to the .npz file created by :meth:`save`.

        Returns
        -------
        EmbeddingIndex
            A fully initialized index ready for search.
        """
        data = np.load(path, allow_pickle=True)

        # Reconstruct without calling __init__
        instance = cls.__new__(cls)
        instance._matrix = data["matrix"]
        instance._idf = data["idf"]
        instance._names = data["names"].tolist()
        instance._vocab = {
            term: idx for idx, term in enumerate(data["vocab_terms"].tolist())
        }
        return instance


# ===================================================================
# Module-level helpers
# ===================================================================

def build_index_from_nodes(nodes: dict[str, dict]) -> EmbeddingIndex:
    """Build a search index from the METASOUND_NODES catalogue.

    Combines each node's name, description, and tags into a single text
    field for TF-IDF indexing.

    Parameters
    ----------
    nodes : dict[str, dict]
        The ``METASOUND_NODES`` dict where each value has ``name``,
        ``description``, and ``tags`` keys.

    Returns
    -------
    EmbeddingIndex
        Ready-to-search index over all nodes.
    """
    entries: list[dict] = []
    for node in nodes.values():
        text_parts = [
            node["name"],
            node.get("description", ""),
            " ".join(node.get("tags", [])),
            node.get("category", ""),
        ]
        entries.append({
            "name": node["name"],
            "text": " ".join(text_parts),
        })
    return EmbeddingIndex(entries)


def build_index_from_mixed(entries: list[dict]) -> EmbeddingIndex:
    """Build a search index from a list of dicts with ``name`` and ``text`` keys.

    This is the general-purpose builder for arbitrary knowledge entries
    (WAAPI functions, Wwise types, audio patterns, etc.).

    Parameters
    ----------
    entries : list[dict]
        Each dict must have ``"name"`` (str) and ``"text"`` (str) keys.

    Returns
    -------
    EmbeddingIndex
        Ready-to-search index over all entries.
    """
    return EmbeddingIndex(entries)
