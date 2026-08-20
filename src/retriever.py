from langchain_core.documents import Document

company_retriever = company_store.as_retriever(search_kwargs={"k": 3})

# 질문으로 관련 문서 검색
results = company_retriever.invoke(question)


def with_chunk_neighbors(hit, window=1):
    m = hit.metadata
    want = [n for n in range(m["chunk_no"] - window,m["chunk_no"] + window + 1)if n >= 0]

    got = company_store.get(
        where={"$and": [{"document_name": {"$eq": m["document_name"]}},
                {"chunk_no": {"$in": want}}]})

    # 조회 결과를 Document 객체로 변환
    documents = [Document(page_content=content,metadata=metadata)
        for metadata, content in zip(got["metadatas"],got["documents"])]

    # chunk_no 순서로 정렬
    return sorted(documents, key=lambda doc: doc.metadata["chunk_no"])

def build_context(results):
    # 1. 각 Document 문자열을 담을 리스트
    context_parts = []
    # 2. 검색된 Document 순회
    for num, doc in enumerate(results, start=1):
        # 3. 검색된 규정 본문
        content = doc.page_content
        # 4. 출처 추적용 chunk_id 
        chunk_id = doc.metadata.get("chunk_id", "출처 없음") #.get()을 사용했기 때문에 chunk_id가 없어도 오류가 발생하지 않음
        # 5. Document 하나를 Context 형태로 구성
        part = f""" 
        [검색 문서 {num} | chunk_id: {chunk_id}]
        {content}
        """ #여러줄의 문자열을 작성할 때에는 쌍따옴표 세번
        # 6. 리스트에 추가 
        context_parts.append(part) 
    # 7. 모든 Document를 하나의 문자열로 결합 
    return "\n\n".join(context_parts)

neighbor_results = with_chunk_neighbors(results[0])
context = build_context(neighbor_results)
print(context)