import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from retriever import StoryIndex, load_index, save_index


USER_DATA_DIR = Path("user_data")


def list_projects() -> List[Dict[str, object]]:
    """List locally saved story projects."""
    USER_DATA_DIR.mkdir(exist_ok=True)
    projects = []

    for project_dir in sorted(USER_DATA_DIR.iterdir()):
        if not project_dir.is_dir():
            continue

        metadata_path = project_dir / "project.json"
        if not metadata_path.exists():
            continue

        projects.append(_read_json(metadata_path))

    return sorted(projects, key=lambda project: str(project.get("updated_at", "")), reverse=True)


def save_project(
    project_name: str,
    manuscript_filename: str,
    chapters: List[Dict[str, object]],
    passages: List[Dict[str, object]],
    index: Optional[StoryIndex] = None,
) -> Dict[str, object]:
    """Save a story project and optional search index under user_data/."""
    project_id = _project_id(project_name)
    project_dir = USER_DATA_DIR / project_id

    if project_dir.exists():
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now().isoformat(timespec="seconds")
    metadata = {
        "project_id": project_id,
        "project_name": project_name,
        "manuscript_filename": manuscript_filename,
        "chapter_count": len(chapters),
        "passage_count": len(passages),
        "created_at": now,
        "updated_at": now,
        "has_semantic_index": index is not None,
    }

    _write_json(project_dir / "project.json", metadata)
    _write_json(project_dir / "chapters.json", chapters)
    _write_json(project_dir / "passages.json", passages)

    if index is not None:
        save_index(index, project_dir / "search_index.pkl")

    return metadata


def load_project(project_id: str) -> Dict[str, object]:
    """Load a story project from user_data/."""
    project_dir = USER_DATA_DIR / project_id
    if not project_dir.exists():
        raise FileNotFoundError(f"Project not found: {project_id}")

    return {
        "metadata": _read_json(project_dir / "project.json"),
        "chapters": _read_json(project_dir / "chapters.json"),
        "passages": _read_json(project_dir / "passages.json"),
        "index": load_index(project_dir / "search_index.pkl"),
    }


def _project_id(project_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", project_name.lower()).strip("-")
    return slug or "untitled-story"


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
