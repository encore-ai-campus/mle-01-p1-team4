import re
from copy import deepcopy
from typing import Any

from bs4 import BeautifulSoup

APPENDIX_PATTERN = re.compile(
    r"(?m)^[ \t]*\[(별표\s*\d+(?:의\s*\d+)?)\][ \t]*$"
)
TABLE_PATTERN = re.compile(r"(?is)<table\b[^>]*>.*?</table>")
RELATED_ARTICLE_PATTERN = re.compile(
    r"\((제\s*\d+\s*조(?:의\s*\d+)?)\s*관련\)"
)
SUBSECTION_PATTERN = re.compile(
    r"(?m)^[ \t]*#{1,6}[ \t]*(\d+\.[ \t]*[^\n<]+)[ \t]*$"
)
ARTICLE_PARTS_PATTERN = re.compile(
    r"(제\s*\d+\s*조(?:의\s*\d+)?)\s*(?:\(([^)]+)\))?"
)


def _clean_text(text: str) -> str:
    soup = BeautifulSoup(text, "html.parser")
    cleaned = soup.get_text("\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n[ \t]+", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def normalize_html_table(table_html: str) -> str:
    soup = BeautifulSoup(table_html, "html.parser")
    rows = soup.find_all("tr")
    if not rows:
        return _clean_text(table_html)

    first_cells = rows[0].find_all(["th", "td"])
    headers = [" ".join(cell.get_text(" ", strip=True).split()) for cell in first_cells]
    has_header = bool(rows[0].find_all("th"))
    data_rows = rows[1:] if has_header else rows

    normalized_rows: list[str] = []
    for row in data_rows:
        cells = [
            " ".join(cell.get_text(" ", strip=True).split())
            for cell in row.find_all(["th", "td"])
        ]
        if not cells:
            continue

        if has_header and len(headers) == len(cells):
            lines = [
                f"{header}: {value}"
                for header, value in zip(headers, cells)
                if header and value
            ]
            normalized_rows.append("\n".join(lines))
        else:
            normalized_rows.append(" | ".join(value for value in cells if value))

    return "\n\n".join(normalized_rows).strip()


def normalize_content(raw_text: str) -> str:
    def replace_table(match: re.Match[str]) -> str:
        return f"\n\n{normalize_html_table(match.group(0))}\n\n"

    text = TABLE_PATTERN.sub(replace_table, raw_text)
    return _clean_text(text)


def parse_article(article: str | None) -> tuple[str | None, str | None]:
    if not article:
        return None, None

    match = ARTICLE_PARTS_PATTERN.search(article)
    if not match:
        return article.strip(), None

    article_no = re.sub(r"\s+", "", match.group(1))
    article_title = match.group(2).strip() if match.group(2) else None
    return article_no, article_title


def _extract_appendix_title(body: str) -> tuple[str | None, str | None]:
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.lower().startswith("<table"):
            break

        heading = re.sub(r"^#{1,6}\s*", "", stripped)
        heading = _clean_text(heading)
        if not heading:
            continue

        related_match = RELATED_ARTICLE_PATTERN.search(heading)
        related_article = None
        if related_match:
            related_article = re.sub(r"\s+", "", related_match.group(1))

        title = RELATED_ARTICLE_PATTERN.sub("", heading).strip()
        return title or None, related_article

    return None, None


def _build_page_content(chunk: dict[str, Any]) -> str:
    context: list[str] = []
    if chunk.get("document_name"):
        context.append(f"문서: {chunk['document_name']}")
    if chunk.get("chapter"):
        context.append(f"장: {_clean_text(str(chunk['chapter']))}")
    if chunk.get("article"):
        context.append(f"조: {_clean_text(str(chunk['article']))}")
    if chunk.get("paragraph"):
        context.append(f"항: {chunk['paragraph']}")
    if chunk.get("appendix_no"):
        context.append(f"별표: {chunk['appendix_no']}")
    if chunk.get("appendix_title"):
        context.append(f"별표 제목: {chunk['appendix_title']}")
    if chunk.get("subsection"):
        context.append(f"구분: {chunk['subsection']}")

    normalized = normalize_content(chunk.get("raw_content") or chunk.get("content") or "")
    if context:
        return "\n".join(context) + "\n\n" + normalized
    return normalized


def _make_main_chunk(source: dict[str, Any], content: str) -> dict[str, Any]:
    chunk = deepcopy(source)
    chunk["content"] = content.strip()
    chunk["raw_content"] = content.strip()
    article_no, article_title = parse_article(chunk.get("article"))
    chunk["article_no"] = article_no
    chunk["article_title"] = article_title
    chunk["section_type"] = "main"
    chunk["chunk_type"] = "paragraph" if chunk.get("paragraph") else "article"
    chunk["appendix_no"] = None
    chunk["appendix_title"] = None
    chunk["subsection"] = None
    chunk["related_article"] = None
    chunk["page_content"] = _build_page_content(chunk)
    return chunk


def _make_appendix_chunks(source: dict[str, Any], appendix_block: str, appendix_no: str) -> list[dict[str, Any]]:
    body = appendix_block.splitlines()
    body_text = "\n".join(body[1:]).strip() if body else ""
    appendix_title, related_article = _extract_appendix_title(body_text)
    subsection_matches = list(SUBSECTION_PATTERN.finditer(body_text))

    chunks: list[dict[str, Any]] = []
    if not subsection_matches:
        chunk = deepcopy(source)
        chunk["chapter"] = None
        chunk["article"] = None
        chunk["paragraph"] = None
        chunk["article_no"] = None
        chunk["article_title"] = None
        chunk["section_type"] = "appendix"
        chunk["chunk_type"] = "table" if TABLE_PATTERN.search(appendix_block) else "appendix"
        chunk["appendix_no"] = appendix_no
        chunk["appendix_title"] = appendix_title
        chunk["subsection"] = None
        chunk["related_article"] = related_article
        chunk["content"] = appendix_block.strip()
        chunk["raw_content"] = appendix_block.strip()
        chunk["page_content"] = _build_page_content(chunk)
        return [chunk]

    prefix = body_text[:subsection_matches[0].start()].strip()
    for index, match in enumerate(subsection_matches):
        start = match.start()
        end = subsection_matches[index + 1].start() if index + 1 < len(subsection_matches) else len(body_text)
        subsection_text = body_text[start:end].strip()
        raw_content = f"{prefix}\n\n{subsection_text}".strip() if prefix else subsection_text

        chunk = deepcopy(source)
        chunk["chapter"] = None
        chunk["article"] = None
        chunk["paragraph"] = None
        chunk["article_no"] = None
        chunk["article_title"] = None
        chunk["section_type"] = "appendix"
        chunk["chunk_type"] = "table" if TABLE_PATTERN.search(raw_content) else "appendix"
        chunk["appendix_no"] = appendix_no
        chunk["appendix_title"] = appendix_title
        chunk["subsection"] = _clean_text(match.group(1))
        chunk["related_article"] = related_article
        chunk["content"] = raw_content
        chunk["raw_content"] = raw_content
        chunk["page_content"] = _build_page_content(chunk)
        chunks.append(chunk)

    return chunks


def split_chunk_on_appendices(source: dict[str, Any]) -> list[dict[str, Any]]:
    content = source.get("content") or source.get("page_content") or ""
    matches = list(APPENDIX_PATTERN.finditer(content))
    if not matches:
        return [_make_main_chunk(source, content)]

    result: list[dict[str, Any]] = []
    main_content = content[:matches[0].start()].strip()
    if main_content:
        result.append(_make_main_chunk(source, main_content))

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        appendix_block = content[start:end].strip()
        appendix_no = re.sub(r"\s+", " ", match.group(1)).strip()
        result.extend(_make_appendix_chunks(source, appendix_block, appendix_no))

    return result


def postprocess_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    processed: list[dict[str, Any]] = []
    counters: dict[str, int] = {}

    for source in chunks:
        for chunk in split_chunk_on_appendices(source):
            document_name = chunk.get("document_name") or "document"
            counters[document_name] = counters.get(document_name, 0) + 1
            chunk["chunk_id"] = f"{document_name}_{counters[document_name]:04d}"
            processed.append(chunk)

    return processed
