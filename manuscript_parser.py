import re
from pathlib import Path
from typing import BinaryIO, Dict, List

from docx import Document


CHAPTER_PATTERN = re.compile(
    r"^("
    r"chapter\s+(?:\d+|[a-z]+|[ivxlcdm]+)\b.*|"
    r"第[0-9一二三四五六七八九十百千两〇零]+[章节回].*|"
    r"(prologue|epilogue)\b.*"
    r")$",
    re.IGNORECASE,
)


def read_txt(file: BinaryIO) -> str:
    """Read a UTF-8 text manuscript."""
    file.seek(0)
    return file.read().decode("utf-8-sig")


def read_docx(file: BinaryIO) -> str:
    """Extract text from a Word manuscript."""
    file.seek(0)
    document = Document(file)

    paragraphs = [
        paragraph.text.strip()
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    return "\n".join(paragraphs)


def read_manuscript(file: BinaryIO, filename: str) -> str:
    """Read a supported manuscript upload."""
    extension = Path(filename).suffix.lower()

    if extension == ".docx":
        return read_docx(file)
    if extension == ".txt":
        return read_txt(file)

    raise ValueError("Only .txt and .docx manuscripts are supported.")


def split_into_chapters(text: str) -> List[Dict[str, object]]:
    """Split manuscript text using English or Chinese chapter headings."""
    chapters = []
    beginning_lines = []
    current_title = None
    current_lines = []

    for line in text.splitlines():
        clean_line = line.strip()

        if clean_line and CHAPTER_PATTERN.match(clean_line):
            if current_title is not None:
                _append_chapter(chapters, current_title, current_lines)
            elif beginning_lines:
                _append_chapter(chapters, "Beginning", beginning_lines)

            current_title = clean_line
            current_lines = []

        elif current_title is None:
            beginning_lines.append(line)
        else:
            current_lines.append(line)

    if current_title is not None:
        _append_chapter(chapters, current_title, current_lines)
    elif text.strip():
        _append_chapter(chapters, "Full Manuscript", text.splitlines())

    return chapters


def split_chapters_into_passages(
    chapters: List[Dict[str, object]],
    max_chars: int = 1400,
    overlap_chars: int = 180,
) -> List[Dict[str, object]]:
    """Divide chapters into smaller searchable passages."""
    passages = []

    for chapter in chapters:
        chapter_text = str(chapter["text"])
        chunks = split_text_into_passages(
            chapter_text,
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        )

        for passage_number, chunk in enumerate(chunks, start=1):
            source_id = f"S{len(passages) + 1}"
            passages.append(
                {
                    "source_id": source_id,
                    "chapter_number": chapter["number"],
                    "chapter_title": chapter["title"],
                    "passage_number": passage_number,
                    "text": chunk,
                }
            )

    return passages


def split_text_into_passages(
    text: str,
    max_chars: int = 1400,
    overlap_chars: int = 180,
) -> List[str]:
    """Split text into readable chunks, preferring paragraph boundaries."""
    paragraphs = [paragraph.strip() for paragraph in text.splitlines() if paragraph.strip()]
    if not paragraphs:
        return []

    chunks = []
    current = ""

    for paragraph in paragraphs:
        next_text = f"{current}\n\n{paragraph}".strip() if current else paragraph

        if len(next_text) <= max_chars:
            current = next_text
            continue

        if current:
            chunks.append(current)
        current = paragraph

        while len(current) > max_chars:
            chunks.append(current[:max_chars].strip())
            current = current[max_chars - overlap_chars :].strip()

    if current:
        chunks.append(current)

    return chunks


def _append_chapter(
    chapters: List[Dict[str, object]],
    title: str,
    lines: List[str],
) -> None:
    text = "\n".join(lines).strip()
    if not text:
        return

    chapters.append(
        {
            "number": len(chapters) + 1,
            "title": title,
            "text": text,
            "word_count": len(text.split()),
            "character_count": len(text),
        }
    )
