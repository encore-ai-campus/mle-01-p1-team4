from langchain_chroma import Chroma
from langchain_core.documents import Document

from ingest import (
    CHROMA_PATH,
    COLLECTION_NAME,
    get_embeddings,
)

def load_vector_store():
    embeddings = get_embeddings()

    store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH,
    )
    return store

def get_retriever(
    store: Chroma,
    k: int = 3,
):
    return store.as_retriever(
        search_kwargs={"k": k}
    )


def with_chunk_neighbors(hit:Document, store: Chroma, window: int = 1) -> list[Document]:
    m = hit.metadata
    want = [n for n in range(m["chunk_no"] - window,m["chunk_no"] + window + 1)if n >= 0]

    got = store.get(
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

def retrieve_context(
    question: str,
    k: int = 3,
    window: int = 1,
):

    store = load_vector_store()

    retriever = get_retriever(
        store=store,
        k=k,
    )

    results = retriever.invoke(question)

    if not results:
        return [], [], ""

    context_docs = []
    seen_chunk_ids = set()

    for hit in results:

        neighbors = with_chunk_neighbors(
            store=store,
            hit=hit,
            window=window,
        )

        for doc in neighbors:
            chunk_id = doc.metadata.get("chunk_id")

            if chunk_id in seen_chunk_ids:
                continue

            seen_chunk_ids.add(chunk_id)
            context_docs.append(doc)

    context = build_context(
        context_docs
    )

    return results, context_docs, context