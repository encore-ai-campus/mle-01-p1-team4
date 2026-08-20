import re
from copy import deepcopy
from typing import Any

from bs4 import BeautifulSoup


APPENDIX_PATTERN = re.compile(
    r"(?m)^[ \t]*\[(별표\s*\d+(?:의\s*\d+)?)\][ \t]*$"
)

TABLE_PATTERN = re.compile(
    r"(?is)<table\b[^>]*>.*?</table>"
)

RELATED_ARTICLE_PATTERN = re.compile(
    r"\((제\s*\d+\s*조(?:의\s*\d+)?)\s*관련\)"
)

SUBSECTION_PATTERN = re.compile(
    r"(?m)^[ \t]*(?:#{1,6}[ \t]*)?(\d+\.[ \t]*[^\n<]+?)[ \t]*$"
)

ARTICLE_PARTS_PATTERN = re.compile(
    r"(제\s*\d+\s*조(?:의\s*\d+)?)\s*(?:\(([^)]+)\))?"
)

SECTION_BOUNDARY_PATTERN = re.compile(
    r"(?m)^[ \t]*(?:"
    r"#{0,6}[ \t]*부\s*칙"
    r"|부칙\s*\("
    r"|\[별표[^\]]*\]"
    r"|\[별지[^\]]*\]"
    r")"
)

APPENDIX_NOTE_PATTERN = re.compile(
    r"(?ms)^(.*?)(?:\n\s*비고\s*:\s*\n?)(.*)$"
)

TRAILING_SECTION_PATTERN = re.compile(
    r"(?m)^[ \t]*(?:"
    r"\[별표[^\]]*\]"
    r"|\[별지[^\]]*\]"
    r")"
)


def _get_content(chunk: dict[str, Any]) -> str:
    """chunk에서 사용할 원본 content를 가져온다."""
    return (
        chunk.get("raw_content")
        or chunk.get("content")
        or ""
    )


def _normalize_whitespace(text: str) -> str:
    """연속된 공백과 줄바꿈을 하나의 공백으로 정규화한다."""
    return re.sub(r"\s+", " ", text).strip()


def _clean_text(text: str) -> str:
    """HTML 태그와 불필요한 공백을 제거한다."""
    soup = BeautifulSoup(text, "html.parser")

    cleaned = soup.get_text("\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n[ \t]+", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


def _split_appendix_core_and_note(
    raw_content: str,
) -> tuple[str, str | None]:
    text = raw_content.strip()

    # 다른 별표 / 별지 / 새로운 번호 제목 시작 시
    # 현재 별표 범위를 종료한다.
    trailing_match = TRAILING_SECTION_PATTERN.search(
        text,
        1,
    )

    if trailing_match:
        text = text[:trailing_match.start()].strip()

    # 비고: 이후 내용은 별도 chunk로 분리한다.
    match = APPENDIX_NOTE_PATTERN.match(text)

    if not match:
        return text, None

    core = match.group(1).strip()
    note = match.group(2).strip()

    return core, note or None


def _appendix_core_key(
    chunk: dict[str, Any],
) -> tuple:
    """
    별표 본문의 중복 판단용 key.
    비고 이후 내용은 제외하고 공통 별표 본문만 비교한다.
    """
    raw_content = _get_content(chunk)

    core, _ = _split_appendix_core_and_note(
        raw_content
    )

    normalized_core = _normalize_whitespace(core)

    return (
        chunk.get("document_name"),
        chunk.get("appendix_no"),
        chunk.get("appendix_title"),
        chunk.get("subsection"),
        normalized_core,
    )


def normalize_html_table(table_html: str) -> str:
    """HTML table을 검색하기 쉬운 텍스트 형태로 변환한다."""
    soup = BeautifulSoup(table_html, "html.parser")
    rows = soup.find_all("tr")

    if not rows:
        return _clean_text(table_html)

    first_cells = rows[0].find_all(["th", "td"])

    headers = [
        " ".join(
            cell.get_text(" ", strip=True).split()
        )
        for cell in first_cells
    ]

    has_header = bool(
        rows[0].find_all("th")
    )

    data_rows = rows[1:] if has_header else rows

    normalized_rows: list[str] = []

    for row in data_rows:
        cells = [
            " ".join(
                cell.get_text(" ", strip=True).split()
            )
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

            normalized_rows.append(
                "\n".join(lines)
            )
        else:
            normalized_rows.append(
                " | ".join(
                    value for value in cells if value
                )
            )

    return "\n\n".join(
        normalized_rows
    ).strip()


def normalize_content(raw_text: str) -> str:
    """본문의 HTML table을 변환하고 전체 텍스트를 정리한다."""

    def replace_table(
        match: re.Match[str],
    ) -> str:
        return (
            "\n\n"
            + normalize_html_table(match.group(0))
            + "\n\n"
        )

    text = TABLE_PATTERN.sub(
        replace_table,
        raw_text,
    )

    return _clean_text(text)


def parse_article(
    article: str | None,
) -> tuple[str | None, str | None]:
    """제N조 형태의 문자열에서 조 번호와 조 제목을 분리한다."""
    if not article:
        return None, None

    match = ARTICLE_PARTS_PATTERN.search(article)

    if not match:
        return article.strip(), None

    article_no = re.sub(
        r"\s+",
        "",
        match.group(1),
    )

    article_title = (
        match.group(2).strip()
        if match.group(2)
        else None
    )

    return article_no, article_title


def _extract_appendix_title(
    body: str,
) -> tuple[str | None, str | None]:
    """별표 제목과 관련 조문을 추출한다."""
    for line in body.splitlines():
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.lower().startswith("<table"):
            break

        heading = re.sub(
            r"^#{1,6}\s*",
            "",
            stripped,
        )

        heading = _clean_text(heading)

        if not heading:
            continue

        related_match = RELATED_ARTICLE_PATTERN.search(
            heading
        )

        related_article = None

        if related_match:
            related_article = re.sub(
                r"\s+",
                "",
                related_match.group(1),
            )

        title = RELATED_ARTICLE_PATTERN.sub(
            "",
            heading,
        ).strip()

        return title or None, related_article

    return None, None


def _build_page_content(
    chunk: dict[str, Any],
) -> str:
    """metadata와 정규화된 본문을 결합해 RAG용 page_content를 만든다."""
    context: list[str] = []

    if chunk.get("document_name"):
        context.append(
            f"문서: {chunk['document_name']}"
        )

    if chunk.get("chapter"):
        context.append(
            f"장: {_clean_text(str(chunk['chapter']))}"
        )

    if chunk.get("article"):
        context.append(
            f"조: {_clean_text(str(chunk['article']))}"
        )

    if chunk.get("paragraph"):
        context.append(
            f"항: {chunk['paragraph']}"
        )

    if chunk.get("appendix_no"):
        context.append(
            f"별표: {chunk['appendix_no']}"
        )

    if chunk.get("appendix_title"):
        context.append(
            f"별표 제목: {chunk['appendix_title']}"
        )

    if chunk.get("subsection"):
        context.append(
            f"구분: {chunk['subsection']}"
        )

    normalized = normalize_content(
        _get_content(chunk)
    )

    if context:
        return (
            "\n".join(context)
            + "\n\n"
            + normalized
        )

    return normalized


def _make_main_chunk(
    source: dict[str, Any],
    content: str,
) -> dict[str, Any]:
    """일반 조문 chunk를 생성한다."""
    chunk = deepcopy(source)

    content = content.strip()

    chunk["content"] = content
    chunk["raw_content"] = content

    article_no, article_title = parse_article(
        chunk.get("article")
    )

    chunk["article_no"] = article_no
    chunk["article_title"] = article_title

    paragraph = chunk.get("paragraph")

    # 기존 parser가 별지의 ①②③ 등을 항으로 잘못 넣은 경우 제거
    if paragraph and paragraph not in content:
        chunk["paragraph"] = None

    chunk["section_type"] = "main"

    chunk["chunk_type"] = (
        "paragraph"
        if chunk.get("paragraph")
        else "article"
    )

    chunk["appendix_no"] = None
    chunk["appendix_title"] = None
    chunk["subsection"] = None
    chunk["related_article"] = None

    chunk["page_content"] = _build_page_content(
        chunk
    )

    return chunk


def _make_appendix_chunks(
    source: dict[str, Any],
    appendix_block: str,
    appendix_no: str,
) -> list[dict[str, Any]]:
    """별표를 하위 구분 단위의 chunk로 분리한다."""
    lines = appendix_block.splitlines()

    body_text = (
        "\n".join(lines[1:]).strip()
        if lines
        else ""
    )

    appendix_title, related_article = (
        _extract_appendix_title(body_text)
    )
    # subsection 탐색 시 비고 영역은 제외한다.
    note_match = APPENDIX_NOTE_PATTERN.match(body_text)

    if note_match:
        subsection_body = note_match.group(1)
    else:
        subsection_body = body_text

    subsection_matches = list(
        SUBSECTION_PATTERN.finditer(subsection_body)
    )

    chunks: list[dict[str, Any]] = []

    # 하위 구분이 없는 별표
    if not subsection_matches:
        chunk = deepcopy(source)

        chunk["chapter"] = None
        chunk["article"] = None
        chunk["paragraph"] = None
        chunk["article_no"] = None
        chunk["article_title"] = None

        chunk["section_type"] = "appendix"

        chunk["chunk_type"] = (
            "table"
            if TABLE_PATTERN.search(appendix_block)
            else "appendix"
        )

        chunk["appendix_no"] = appendix_no
        chunk["appendix_title"] = appendix_title
        chunk["subsection"] = None
        chunk["related_article"] = related_article

        content = appendix_block.strip()

        chunk["content"] = content
        chunk["raw_content"] = content
        chunk["page_content"] = _build_page_content(
            chunk
        )

        return [chunk]

    # 별표 제목 부분만 공통 정보로 보존
    header_text = subsection_body[
        :subsection_matches[0].start()
    ].strip()


    for index, match in enumerate(
    subsection_matches
    ):
        start = match.start()

        end = (
            subsection_matches[index + 1].start()
            if index + 1 < len(subsection_matches)
            else len(subsection_body)
        )

        subsection_text = subsection_body[
            start:end
        ].strip()

        # 첫 subsection 앞에 있던 공통 내용은
        # 첫 번째 chunk에 포함시켜 유실을 방지한다.
        if index == 0 and header_text:
            subsection_text = (
                header_text
                + "\n\n"
                + subsection_text
            )

        if not subsection_text:
            continue

        chunk = deepcopy(source)

        chunk["chapter"] = None
        chunk["article"] = None
        chunk["paragraph"] = None
        chunk["article_no"] = None
        chunk["article_title"] = None

        chunk["section_type"] = "appendix"

        chunk["chunk_type"] = (
            "table"
            if TABLE_PATTERN.search(subsection_text)
            else "appendix"
        )

        chunk["appendix_no"] = appendix_no
        chunk["appendix_title"] = appendix_title
        chunk["subsection"] = _clean_text(
            match.group(1)
        )
        chunk["related_article"] = related_article

        # 첫 subsection 내용을 다른 subsection에
        # prefix로 반복하지 않는다.
        chunk["content"] = subsection_text
        chunk["raw_content"] = subsection_text

        chunk["page_content"] = _build_page_content(
            chunk
        )

        chunks.append(chunk)

    return chunks


def split_chunk_on_appendices(
    source: dict[str, Any],
) -> list[dict[str, Any]]:
    """본문과 부칙/별표/별지를 분리하고 별표 chunk를 생성한다."""
    content = (
        source.get("content")
        or source.get("page_content")
        or ""
    )

    # 1. 먼저 부칙 / 별표 / 별지 시작 위치를 찾는다.
    boundary_match = SECTION_BOUNDARY_PATTERN.search(
        content
    )

    if boundary_match:
        main_content = content[
            :boundary_match.start()
        ].strip()

        trailing_content = content[
            boundary_match.start():
        ].strip()
    else:
        main_content = content.strip()
        trailing_content = ""

    result: list[dict[str, Any]] = []

    # 2. 조문 본문은 경계 이전까지만 main chunk로 만든다.
    if main_content:
        result.append(
            _make_main_chunk(
                source,
                main_content,
            )
        )

    # 3. 뒤쪽 내용에서 별표만 별도 처리한다.
    if trailing_content:
        appendix_matches = list(
            APPENDIX_PATTERN.finditer(
                trailing_content
            )
        )

        for index, match in enumerate(
            appendix_matches
        ):
            start = match.start()

            end = (
                appendix_matches[index + 1].start()
                if index + 1 < len(appendix_matches)
                else len(trailing_content)
            )

            appendix_block = trailing_content[
                start:end
            ].strip()

            appendix_no = _normalize_whitespace(
                match.group(1)
            )

            result.extend(
                _make_appendix_chunks(
                    source,
                    appendix_block,
                    appendix_no,
                )
            )

    return result


def _dedup_key(
    chunk: dict[str, Any],
) -> tuple:
    """일반 chunk의 중복 판단용 key를 생성한다."""
    normalized_content = _normalize_whitespace(
        _get_content(chunk)
    )

    return (
        chunk.get("document_name"),
        chunk.get("article_no"),
        chunk.get("paragraph"),
        normalized_content,
    )


def postprocess_chunks(
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """전체 chunk를 분리, 중복 제거하고 chunk_id를 부여한다."""

    # 1. 기존 별표/본문 분리
    split_result: list[dict[str, Any]] = []

    for source in chunks:
        split_result.extend(
            split_chunk_on_appendices(source)
        )

    processed: list[dict[str, Any]] = []

    # 일반 chunk dedup
    seen_general: set[tuple] = set()

    # 별표 본문 dedup
    seen_appendix_core: set[tuple] = set()

    # 별표 note dedup
    seen_appendix_notes: set[tuple] = set()

    for chunk in split_result:

        # ---------------------------------
        # 일반 chunk 처리
        # ---------------------------------
        if chunk.get("section_type") != "appendix":
            key = _dedup_key(chunk)

            if key in seen_general:
                continue

            seen_general.add(key)
            processed.append(chunk)

            continue

        # ---------------------------------
        # 별표 처리
        # ---------------------------------
        raw_content = _get_content(chunk)

        core, note = (
            _split_appendix_core_and_note(
                raw_content
            )
        )

        core_key = _appendix_core_key(chunk)

        # 동일 별표 본문은 최초 1번만 저장
        if core_key not in seen_appendix_core:
            core_chunk = deepcopy(chunk)

            core_chunk["content"] = core
            core_chunk["raw_content"] = core

            core_chunk["page_content"] = (
                _build_page_content(core_chunk)
            )

            seen_appendix_core.add(core_key)
            processed.append(core_chunk)

        # 비고 부분이 있으면 별도 chunk로 저장
        if note:
            normalized_note = (
                _normalize_whitespace(note)
            )

            note_key = (
                chunk.get("document_name"),
                chunk.get("appendix_no"),
                chunk.get("appendix_title"),
                normalized_note,
            )

            if note_key not in seen_appendix_notes:
                note_chunk = deepcopy(chunk)

                note_chunk["chunk_type"] = (
                    "appendix_note"
                )

                note_chunk["subsection"] = "비고"

                note_chunk["content"] = note
                note_chunk["raw_content"] = note

                note_chunk["page_content"] = (
                    _build_page_content(note_chunk)
                )

                seen_appendix_notes.add(note_key)
                processed.append(note_chunk)

    # 4. 최종 chunk_id 재부여
    counters: dict[str, int] = {}

    for chunk in processed:
        document_name = (
            chunk.get("document_name")
            or "document"
        )

        counters[document_name] = (
            counters.get(document_name, 0) + 1
        )
        chunk["chunk_no"] = counters[document_name]

        chunk["chunk_id"] = (
            f"{document_name}_"
            f"{counters[document_name]:04d}"
        )

    return processed