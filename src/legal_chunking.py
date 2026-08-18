import re
from bs4 import BeautifulSoup

CHAPTER_PATTERN = re.compile(
    r"(?m)^[ \t]*#{0,6}[ \t]*(제\s*\d+\s*장(?:\s+[^\n]+)?)"
)
ARTICLE_PATTERN = re.compile(
    r"(?m)^[ \t]*#{0,6}[ \t]*(제\s*\d+\s*조(?:의\s*\d+)?(?:\s*\([^)\n]+\))?)"
)
PARAGRAPH_PATTERN = re.compile(r"[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]")
APPENDIX_PATTERN = re.compile(r"(?m)^[ \t]*\[(별표\s*\d+(?:의\s*\d+)?)\][ \t]*$")
APPENDIX_SUBSECTION_PATTERN = re.compile(
    r"(?m)^[ \t]*#{0,6}[ \t]*(\d+\.[ \t]*[^\n<]+)[ \t]*$"
)
TABLE_PATTERN = re.compile(r"(?is)<table\b[^>]*>.*?</table>")
RELATED_ARTICLE_PATTERN = re.compile(r"\((제\s*\d+\s*조(?:의\s*\d+)?)[ \t]*관련\)")


def _clean_inline_html(text: str) -> str:
    soup = BeautifulSoup(text, "html.parser")
    return " ".join(soup.get_text(" ", strip=True).split())


def normalize_html_table(table_html: str) -> str:
    soup = BeautifulSoup(table_html, "html.parser")
    rows = soup.find_all("tr")
    if not rows:
        return _clean_inline_html(table_html)

    first_cells = rows[0].find_all(["th", "td"])
    headers = [" ".join(cell.get_text(" ", strip=True).split()) for cell in first_cells]
    has_header = bool(rows[0].find_all("th"))
    data_rows = rows[1:] if has_header else rows

    normalized_rows = []
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
    def replace_table(match: re.Match) -> str:
        normalized = normalize_html_table(match.group(0))
        return f"\n\n{normalized}\n\n"

    text = TABLE_PATTERN.sub(replace_table, raw_text)
    text = BeautifulSoup(text, "html.parser").get_text("\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _article_parts(article_name: str):
    match = re.match(
        r"(제\s*\d+\s*조(?:의\s*\d+)?)\s*(?:\(([^)]+)\))?",
        article_name,
    )
    if not match:
        return article_name, None
    return match.group(1).replace(" ", ""), match.group(2)


def _contextualize(document_name, content, chapter=None, article=None,
                   paragraph=None, appendix_no=None, appendix_title=None,
                   subsection=None):
    context = [f"문서: {document_name}"]
    if chapter:
        context.append(f"장: {_clean_inline_html(chapter)}")
    if article:
        context.append(f"조: {_clean_inline_html(article)}")
    if paragraph:
        context.append(f"항: {paragraph}")
    if appendix_no:
        context.append(f"별표: {appendix_no}")
    if appendix_title:
        context.append(f"별표 제목: {appendix_title}")
    if subsection:
        context.append(f"구분: {subsection}")
    return "\n".join(context) + "\n\n" + normalize_content(content)


def _split_articles(text: str, document_name: str):
    chunks = []
    chapter_matches = list(CHAPTER_PATTERN.finditer(text)) or [None]

    for chapter_index, chapter_match in enumerate(chapter_matches):
        if chapter_match:
            chapter_name = chapter_match.group(1).strip()
            chapter_start = chapter_match.start()
            chapter_end = (
                chapter_matches[chapter_index + 1].start()
                if chapter_index + 1 < len(chapter_matches)
                else len(text)
            )
            chapter_text = text[chapter_start:chapter_end]
        else:
            chapter_name = None
            chapter_text = text

        article_matches = list(ARTICLE_PATTERN.finditer(chapter_text))
        for article_index, article_match in enumerate(article_matches):
            article_name = article_match.group(1).strip()
            article_no, article_title = _article_parts(article_name)
            article_start = article_match.start()
            article_end = (
                article_matches[article_index + 1].start()
                if article_index + 1 < len(article_matches)
                else len(chapter_text)
            )
            article_text = chapter_text[article_start:article_end].strip()
            if not article_text:
                continue

            paragraph_matches = list(PARAGRAPH_PATTERN.finditer(article_text))
            if not paragraph_matches:
                chunks.append({
                    "document_name": document_name,
                    "section_type": "main",
                    "chunk_type": "article",
                    "chapter": chapter_name,
                    "article": article_name,
                    "article_no": article_no,
                    "article_title": article_title,
                    "paragraph": None,
                    "appendix_no": None,
                    "appendix_title": None,
                    "subsection": None,
                    "related_article": None,
                    "raw_content": article_text,
                    "page_content": _contextualize(
                        document_name, article_text,
                        chapter=chapter_name, article=article_name,
                    ),
                })
                continue

            for paragraph_index, paragraph_match in enumerate(paragraph_matches):
                paragraph_start = paragraph_match.start()
                paragraph_end = (
                    paragraph_matches[paragraph_index + 1].start()
                    if paragraph_index + 1 < len(paragraph_matches)
                    else len(article_text)
                )
                paragraph_text = article_text[paragraph_start:paragraph_end].strip()
                if not paragraph_text:
                    continue
                paragraph_symbol = paragraph_match.group(0)
                chunks.append({
                    "document_name": document_name,
                    "section_type": "main",
                    "chunk_type": "paragraph",
                    "chapter": chapter_name,
                    "article": article_name,
                    "article_no": article_no,
                    "article_title": article_title,
                    "paragraph": paragraph_symbol,
                    "appendix_no": None,
                    "appendix_title": None,
                    "subsection": None,
                    "related_article": None,
                    "raw_content": paragraph_text,
                    "page_content": _contextualize(
                        document_name, paragraph_text,
                        chapter=chapter_name, article=article_name,
                        paragraph=paragraph_symbol,
                    ),
                })
    return chunks


def _extract_appendix_title(block_body: str):
    for line in block_body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("<table"):
            break
        heading = re.sub(r"^#{1,6}\s*", "", stripped)
        heading = _clean_inline_html(heading)
        if heading:
            related = RELATED_ARTICLE_PATTERN.search(heading)
            related_article = related.group(1).replace(" ", "") if related else None
            title = RELATED_ARTICLE_PATTERN.sub("", heading).strip()
            return title, related_article
    return None, None


def _split_appendices(text: str, document_name: str):
    chunks = []
    matches = list(APPENDIX_PATTERN.finditer(text))
    for index, match in enumerate(matches):
        appendix_no = re.sub(r"\s+", " ", match.group(1)).strip()
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        body = text[match.end():end].strip()
        appendix_title, related_article = _extract_appendix_title(body)

        subsection_matches = list(APPENDIX_SUBSECTION_PATTERN.finditer(body))
        if not subsection_matches:
            chunks.append({
                "document_name": document_name,
                "section_type": "appendix",
                "chunk_type": "table" if TABLE_PATTERN.search(block) else "appendix",
                "chapter": None,
                "article": None,
                "article_no": None,
                "article_title": None,
                "paragraph": None,
                "appendix_no": appendix_no,
                "appendix_title": appendix_title,
                "subsection": None,
                "related_article": related_article,
                "raw_content": block,
                "page_content": _contextualize(
                    document_name, block,
                    appendix_no=appendix_no,
                    appendix_title=appendix_title,
                ),
            })
            continue

        prefix = body[:subsection_matches[0].start()].strip()
        for subsection_index, subsection_match in enumerate(subsection_matches):
            subsection = _clean_inline_html(subsection_match.group(1).strip())
            subsection_start = subsection_match.start()
            subsection_end = (
                subsection_matches[subsection_index + 1].start()
                if subsection_index + 1 < len(subsection_matches)
                else len(body)
            )
            subsection_text = body[subsection_start:subsection_end].strip()
            raw_content = (prefix + "\n\n" + subsection_text).strip() if prefix else subsection_text
            chunks.append({
                "document_name": document_name,
                "section_type": "appendix",
                "chunk_type": "table" if TABLE_PATTERN.search(raw_content) else "appendix",
                "chapter": None,
                "article": None,
                "article_no": None,
                "article_title": None,
                "paragraph": None,
                "appendix_no": appendix_no,
                "appendix_title": appendix_title,
                "subsection": subsection,
                "related_article": related_article,
                "raw_content": raw_content,
                "page_content": _contextualize(
                    document_name, raw_content,
                    appendix_no=appendix_no,
                    appendix_title=appendix_title,
                    subsection=subsection,
                ),
            })
    return chunks


def split_legal_document(document_text: str, document_name: str):
    appendix_matches = list(APPENDIX_PATTERN.finditer(document_text))
    main_text = (
        document_text[:appendix_matches[0].start()]
        if appendix_matches
        else document_text
    )
    chunks = _split_articles(main_text, document_name)
    if appendix_matches:
        chunks.extend(_split_appendices(document_text[appendix_matches[0].start():], document_name))
    return chunks
