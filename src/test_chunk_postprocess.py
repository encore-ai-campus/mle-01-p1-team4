import json
from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC_DIR))

from legal_chunking import normalize_html_table, postprocess_chunks


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
                "<table><tr><th>직급</th><th>기준</th></tr>"
                "<tr><td>2급</td><td>경력 6년 이상</td></tr></table>"
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
            "content": "제5조(운영체계)\n② 공간정보 보안담당관은 AI디지털전략실장이 된다.",
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
    assert chunk["article_no"] == "제5조"
    assert chunk["article_title"] == "운영체계"
    assert chunk["section_type"] == "main"
    assert chunk["chunk_type"] == "paragraph"
    assert chunk["chunk_id"] == "공간정보보안업무예규_0001"
