import os
from typing import List, Optional

from retriever import SearchResult


DEFAULT_OPENAI_MODEL = "gpt-5.4-mini"


def has_api_key() -> bool:
    _load_environment()
    return bool(os.getenv("OPENAI_API_KEY"))


def answer_question(
    question: str,
    results: List[SearchResult],
    model: Optional[str] = None,
) -> Optional[str]:
    """Generate an evidence-based answer with the OpenAI Responses API."""
    _load_environment()

    if not os.getenv("OPENAI_API_KEY"):
        return None

    from openai import OpenAI

    client = OpenAI()
    selected_model = model or os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    response = client.responses.create(
        model=selected_model,
        instructions=(
            "You are Story Thread Tracker, an assistant for long-form writers. "
            "Answer only from the provided manuscript passages. "
            "If the evidence is not enough, say what is missing. "
            "Cite supporting passages using source IDs like [S1] and [S2]."
        ),
        input=_build_prompt(question, results),
    )

    return getattr(response, "output_text", None) or str(response)


def _load_environment() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
        return
    except ImportError:
        pass

    env_path = ".env"
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as file:
        for line in file:
            clean_line = line.strip()
            if not clean_line or clean_line.startswith("#") or "=" not in clean_line:
                continue
            key, value = clean_line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def _build_prompt(question: str, results: List[SearchResult]) -> str:
    evidence_blocks = []

    for result in results:
        evidence_blocks.append(
            "\n".join(
                [
                    f"[{result.source_id}]",
                    f"Chapter: {result.chapter_title}",
                    f"Passage: {result.passage_number}",
                    "Text:",
                    result.text,
                ]
            )
        )

    evidence = "\n\n---\n\n".join(evidence_blocks)

    return (
        f"Question:\n{question}\n\n"
        f"Manuscript evidence:\n{evidence}\n\n"
        "Write a concise answer for the writer. "
        "Use citations after claims that depend on the manuscript evidence."
    )
