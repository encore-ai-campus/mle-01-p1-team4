from src.preprocessing.legal_chunking import (
    normalize_html_table,
    postprocess_chunks,
    split_chunk_on_appendices,
)


def test_normalize_html_table_preserves_header_value_relationships():
    html = """
    <table>
      <tr><th>직급</th><th>기준</th></tr>
      <tr><td>2급</td><td>지적기사 경력 6년 이상</td></tr>
    </table>
    """

    result = normalize_html_table(html)

    assert "직급: 2급" in result
    assert "기준: 지적기사 경력 6년 이상" in result
    assert "<table" not in result


def test_postprocess_splits_appendix_from_previous_article():
    chunks = [
        {
            "article": "제3조 (경과조치)",
            "paragraph": None,
            "content": (
                "제3조 (경과조치) 본문 내용입니다.\n\n"
                "[별표 1]\n\n"
                "# 신규 채용자 자격기준 (제13조 관련)\n\n"
                "## 1. 국토정보직\n\n"
                "<table>"
                "<tr><th>직급</th><th>기준</th></tr>"
                "<tr><td>2급</td><td>경력 6년 이상</td></tr>"
                "</table>"
            ),
            "document_name": "인사규정",
            "chapter": "제10장 보칙",
            "chunk_id": "인사규정_0186",
            "source_file": "인사규정_파싱결과.json",
        }
    ]

    result = postprocess_chunks(chunks)

    assert len(result) == 2

    article_chunk, appendix_chunk = result

    assert article_chunk["section_type"] == "main"
    assert "[별표 1]" not in article_chunk["content"]

    assert appendix_chunk["section_type"] == "appendix"
    assert appendix_chunk["appendix_no"] == "별표 1"
    assert appendix_chunk["appendix_title"] == "신규 채용자 자격기준"
    assert appendix_chunk["related_article"] == "제13조"
    assert appendix_chunk["subsection"] == "1. 국토정보직"

    assert "직급: 2급" in appendix_chunk["page_content"]
    assert "<table" not in appendix_chunk["page_content"]
    assert "<table" in appendix_chunk["raw_content"]


def test_postprocess_preserves_existing_metadata_and_reassigns_chunk_ids():
    chunks = [
        {
            "article": "제5조(운영체계)",
            "paragraph": "②",
            "content": (
                "제5조(운영체계)\n"
                "② 공간정보 보안담당관은 "
                "AI디지털전략실장이 된다."
            ),
            "document_name": "공간정보보안업무예규",
            "chapter": "제2장 공간정보 보안 관리체계",
            "chunk_id": "공간정보보안업무예규_0006",
            "source_file": "공간정보보안업무예규_파싱결과.json",
        }
    ]

    result = postprocess_chunks(chunks)

    assert len(result) == 1

    chunk = result[0]

    assert chunk["document_name"] == "공간정보보안업무예규"
    assert chunk["source_file"] == "공간정보보안업무예규_파싱결과.json"

    assert chunk["article_no"] == "제5조"
    assert chunk["article_title"] == "운영체계"

    assert chunk["paragraph"] == "②"
    assert chunk["section_type"] == "main"
    assert chunk["chunk_type"] == "paragraph"

    assert chunk["chunk_id"] == "공간정보보안업무예규_0001"

    assert "문서: 공간정보보안업무예규" in chunk["page_content"]
    assert "조: 제5조(운영체계)" in chunk["page_content"]
    assert "항: ②" in chunk["page_content"]


def test_appendix_subsections_are_split_independently():
    source = {
        "document_name": "인사규정",
        "content": """
[별표 1]

# 신규 채용자 자격기준 (제13조 관련)

1. 국토정보직

<table>
<tr><th>직 급</th><th>기 준</th></tr>
<tr><td>1 급</td><td>국토정보직 기준</td></tr>
</table>

## 2. 기획경영직

<table>
<tr><th>직 급</th><th>기 준</th></tr>
<tr><td>1 급</td><td>기획경영직 기준</td></tr>
</table>
"""
    }

    chunks = split_chunk_on_appendices(source)

    assert len(chunks) == 2

    first_chunk = chunks[0]
    second_chunk = chunks[1]

    assert first_chunk["subsection"] == "1. 국토정보직"
    assert "국토정보직 기준" in first_chunk["raw_content"]
    assert "기획경영직 기준" not in first_chunk["raw_content"]

    assert second_chunk["subsection"] == "2. 기획경영직"
    assert "기획경영직 기준" in second_chunk["raw_content"]
    assert "국토정보직 기준" not in second_chunk["raw_content"]

    assert first_chunk["appendix_no"] == "별표 1"
    assert second_chunk["appendix_no"] == "별표 1"

    assert first_chunk["appendix_title"] == "신규 채용자 자격기준"
    assert second_chunk["appendix_title"] == "신규 채용자 자격기준"

    assert first_chunk["related_article"] == "제13조"
    assert second_chunk["related_article"] == "제13조"

    assert "<table" not in first_chunk["page_content"]
    assert "<table" not in second_chunk["page_content"]

    assert "직 급: 1 급" in first_chunk["page_content"]
    assert "직 급: 1 급" in second_chunk["page_content"]

def test_postprocess_removes_exact_duplicate_appendices():
    chunks = [
        {
            "document_name": "급여규정",
            "content": (
                "[별표 2]\n\n"
                "직원 봉급액(제4조 관련)\n\n"
                "<table>"
                "<tr><th>호봉</th><th>3급</th></tr>"
                "<tr><td>1</td><td>4,909,000</td></tr>"
                "</table>"
            ),
        },
        {
            "document_name": "급여규정",
            "content": (
                "[별표 2]\n\n"
                "직원 봉급액(제4조 관련)\n\n"
                "<table>"
                "<tr><th>호봉</th><th>3급</th></tr>"
                "<tr><td>1</td><td>4,909,000</td></tr>"
                "</table>"
            ),
        },
    ]

    result = postprocess_chunks(chunks)

    assert len(result) == 1
    assert result[0]["appendix_no"] == "별표 2"