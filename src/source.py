#1. 출처 만드는 함수 정의
def build_sources(documents):
    # 최종 출력할 출처
    sources = []

    # 이미 추가한 조문/별표를 기억
    seen_sources = set()

    for doc in documents:
        metadata = doc.metadata
        # 문서명 가져오기
        document_name = metadata.get("document_name","문서명 없음",)
        section_type = metadata.get("section_type")
        chunk_id = metadata.get("chunk_id")         
        if section_type == "main":
            article_no = metadata.get("article_no") 
            source_key = f"{document_name} {article_no}"

        elif section_type == "appendix":
            appendix_no = metadata.get("appendix_no")
            appendix_title = metadata.get("appendix_title")
            source_key = f"{document_name} {appendix_no} - {appendix_title}"  

        else:
            source_key = document_name

        # 같은 조문이나 별표가 이미 추가됐다면 건너뛰기
        if source_key in seen_sources:
            continue

        # 처음 발견된 출처라고 기록
        seen_sources.add(source_key)

        # 화면 표시용 출처에만 chunk_id 추가  -> 개발 완료 후 제거!
        if chunk_id:
            source = f"{source_key} [{chunk_id}]"
        else:
            source = source_key

        # 출처 문자열 추가
        sources.append(source)

    return "\n".join(
        f"- {source}"
        for source in sources
    )

