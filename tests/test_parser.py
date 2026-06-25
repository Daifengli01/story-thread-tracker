from manuscript_parser import split_chapters_into_passages, split_into_chapters


def test_detects_english_chapters():
    text = """Chapter 1

The sword slept under the altar.

Chapter 2

The sword began speaking at night.
"""

    chapters = split_into_chapters(text)

    assert len(chapters) == 2
    assert chapters[0]["title"] == "Chapter 1"
    assert "altar" in chapters[0]["text"]


def test_detects_chinese_chapters():
    text = """第一章 风起

陆有期进入山门。

第二章 神火

他看见神火落下。
"""

    chapters = split_into_chapters(text)

    assert len(chapters) == 2
    assert chapters[0]["title"] == "第一章 风起"
    assert "神火" in chapters[1]["text"]


def test_creates_searchable_passages():
    text = """Chapter 1

First paragraph.

Second paragraph.
"""

    chapters = split_into_chapters(text)
    passages = split_chapters_into_passages(chapters, max_chars=40, overlap_chars=5)

    assert passages
    assert passages[0]["source_id"] == "S1"
    assert passages[0]["chapter_title"] == "Chapter 1"
