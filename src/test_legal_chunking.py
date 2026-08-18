from legal_chunking import normalize_html_table, split_legal_document


def test_appendix_is_not_swallowed_by_previous_article():
    text = '''
# 제10장 보 칙
제3조 (경과조치) 이 규정 시행 당시 종전 규정에 따른다.

[별표 1]
# 신규 채용자 자격기준 (제13조 관련)
<table>
<tr><th>직급</th><th>기준</th></tr>
<tr><td>2급</td><td>지적기사 경력 6년 이상</td></tr>
</table>
'''
    chunks = split_legal_document(text, '인사규정')
    assert len(chunks) == 2
    article_chunk = chunks[0]
    appendix_chunk = chunks[1]
    assert article_chunk['section_type'] == 'main'
    assert '[별표 1]' not in article_chunk['page_content']
    assert appendix_chunk['section_type'] == 'appendix'
    assert appendix_chunk['appendix_no'] == '별표 1'


def test_table_normalization_preserves_header_value_relationship():
    html = '''<table>
<tr><th>직급</th><th>기준</th></tr>
<tr><td>2급</td><td>지적기사 경력 6년 이상</td></tr>
</table>'''
    normalized = normalize_html_table(html)
    assert '직급: 2급' in normalized
    assert '기준: 지적기사 경력 6년 이상' in normalized
    assert '<table>' not in normalized


def test_paragraph_metadata_keeps_original_symbol():
    text = '''
# 제2장 공간정보 보안 관리체계
제5조(운영체계)
① 첫 번째 항이다.
② 두 번째 항이다.
'''
    chunks = split_legal_document(text, '공간정보보안업무예규')
    assert [chunk['paragraph'] for chunk in chunks] == ['①', '②']
