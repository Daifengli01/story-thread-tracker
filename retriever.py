import math
import os
import pickle
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np


DEFAULT_EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "chapter",
    "chapters",
    "did",
    "do",
    "does",
    "for",
    "from",
    "he",
    "her",
    "him",
    "his",
    "how",
    "i",
    "in",
    "is",
    "it",
    "mention",
    "mentions",
    "of",
    "on",
    "or",
    "she",
    "the",
    "their",
    "them",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


@dataclass
class SearchResult:
    source_id: str
    chapter_number: int
    chapter_title: str
    passage_number: int
    text: str
    score: float
    keyword_score: float
    semantic_score: float


@dataclass
class StoryIndex:
    model_name: str
    passages: List[Dict[str, object]]
    embeddings: np.ndarray


def build_index(passages: List[Dict[str, object]]) -> StoryIndex:
    """Build a local multilingual semantic-search index."""
    model_name = os.getenv("STT_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
    model = _load_embedding_model(model_name)
    texts = [_passage_search_text(passage) for passage in passages]
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    embeddings = _normalize_matrix(embeddings)
    return StoryIndex(model_name=model_name, passages=passages, embeddings=embeddings)


def save_index(index: StoryIndex, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as file:
        pickle.dump(index, file)


def load_index(path: Path) -> Optional[StoryIndex]:
    if not path.exists():
        return None

    with path.open("rb") as file:
        return pickle.load(file)


def search_index(
    index: StoryIndex,
    question: str,
    top_k: int = 10,
) -> List[SearchResult]:
    """Search passages using semantic similarity plus keyword overlap."""
    model = _load_embedding_model(index.model_name)
    question_embedding = model.encode([question], convert_to_numpy=True, show_progress_bar=False)
    question_embedding = _normalize_matrix(question_embedding)[0]
    semantic_scores = index.embeddings @ question_embedding
    keyword_scores = _keyword_scores(question, index.passages)

    results = []
    for position, passage in enumerate(index.passages):
        semantic_score = float(semantic_scores[position])
        keyword_score = keyword_scores[position]
        combined_score = (semantic_score * 0.75) + (keyword_score * 0.25)

        if combined_score <= 0:
            continue

        results.append(_make_result(passage, combined_score, keyword_score, semantic_score))

    return sorted(results, key=lambda result: result.score, reverse=True)[:top_k]


def keyword_search(
    passages: List[Dict[str, object]],
    question: str,
    top_k: int = 10,
) -> List[SearchResult]:
    """Search passages without embeddings."""
    keyword_scores = _keyword_scores(question, passages)
    results = []

    for position, passage in enumerate(passages):
        keyword_score = keyword_scores[position]
        if keyword_score <= 0:
            continue
        results.append(_make_result(passage, keyword_score, keyword_score, 0.0))

    return sorted(results, key=lambda result: result.score, reverse=True)[:top_k]


def _load_embedding_model(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def _keyword_scores(question: str, passages: List[Dict[str, object]]) -> List[float]:
    terms = _question_terms(question)
    if not terms:
        return [0.0 for _ in passages]

    raw_scores = []
    for passage in passages:
        text = _passage_search_text(passage).lower()
        count = sum(text.count(term) for term in terms)
        raw_scores.append(float(count))

    highest = max(raw_scores, default=0.0)
    if highest <= 0:
        return raw_scores

    return [score / highest for score in raw_scores]


def _question_terms(question: str) -> List[str]:
    tokens = re.findall(r"[\w\u4e00-\u9fff']+", question.lower())
    terms = []

    for token in tokens:
        if token in STOP_WORDS or len(token) <= 1:
            continue
        terms.append(token)

    return terms


def _passage_search_text(passage: Dict[str, object]) -> str:
    return (
        f"{passage['chapter_title']}\n"
        f"Passage {passage['passage_number']}\n"
        f"{passage['text']}"
    )


def _normalize_matrix(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return matrix / norms


def _make_result(
    passage: Dict[str, object],
    score: float,
    keyword_score: float,
    semantic_score: float,
) -> SearchResult:
    return SearchResult(
        source_id=str(passage["source_id"]),
        chapter_number=int(passage["chapter_number"]),
        chapter_title=str(passage["chapter_title"]),
        passage_number=int(passage["passage_number"]),
        text=str(passage["text"]),
        score=round(float(score), 4),
        keyword_score=round(float(keyword_score), 4),
        semantic_score=round(float(semantic_score), 4),
    )
