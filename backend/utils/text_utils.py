import re

CHAPTER_PATTERNS = [
    re.compile(r"^第[一二三四五六七八九十百千万零]+章(?:\s+(.*))?$"),
    re.compile(r"^第[0-9]+章(?:\s+(.*))?$"),
    re.compile(r"^第[0-9]+节(?:\s+(.*))?$"),
    re.compile(r"^Chapter\s+[0-9]+(?:\s+(.*))?$", re.IGNORECASE),
]

MAX_CHAPTER_CHARS = 8000


def _has_chapter_headers(content: str) -> bool:
    for line in content.split("\n"):
        stripped = line.strip()
        for pattern in CHAPTER_PATTERNS:
            if pattern.match(stripped):
                return True
    return False


def _split_by_size(content: str) -> list[dict]:
    paragraphs = [p for p in content.split("\n") if p.strip()]
    chapters = []
    current = []
    length = 0
    chapter_num = 1
    for p in paragraphs:
        if length + len(p) > MAX_CHAPTER_CHARS:
            if current:
                chapters.append({
                    "title": f"第{chapter_num}章",
                    "content": "\n".join(current),
                })
                chapter_num += 1
            current = [p]
            length = len(p)
        else:
            current.append(p)
            length += len(p)
    if current:
        chapters.append({
            "title": f"第{chapter_num}章",
            "content": "\n".join(current),
        })
    return chapters


def split_into_chapters(content: str) -> list[dict]:
    lines = content.split("\n")
    chapters = []
    current_title = "开头"
    current_content = []

    for line in lines:
        stripped = line.strip()
        matched = False
        for pattern in CHAPTER_PATTERNS:
            m = pattern.match(stripped)
            if m:
                if current_content:
                    chapters.append({
                        "title": current_title,
                        "content": "\n".join(current_content).strip(),
                    })
                current_title = stripped
                current_content = []
                matched = True
                break
        if not matched:
            current_content.append(line)

    if current_content:
        chapters.append({
            "title": current_title,
            "content": "\n".join(current_content).strip(),
        })

    # No chapter headers found → split by size
    if not _has_chapter_headers(content):
        return _split_by_size(content)

    # Any single chapter too large → force split all by size
    oversized = [c for c in chapters if len(c["content"]) > MAX_CHAPTER_CHARS]
    if oversized:
        all_text = "\n".join(c["content"] for c in chapters)
        return _split_by_size(all_text)

    return chapters


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in text.split("\n") if p.strip()]


def count_words(text: str) -> int:
    return len(text.replace("\n", "").replace(" ", "").replace("\r", ""))
