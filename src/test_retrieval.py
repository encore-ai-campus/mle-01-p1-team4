# test_retrieval.py

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


CHROMA_PATH = "chroma/ko-sroberta/"
COLLECTION_NAME = "company_regulations"
EMBEDDING_MODEL = "jhgan/ko-sroberta-multitask"


def load_vector_store() -> Chroma:

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH,
    )

    return store


def test_search(
    store: Chroma,
    query: str,
    k: int = 3,
):

    results = store.similarity_search(
        query,
        k=k,
    )

    print("\n질문:", query)
    print("검색 결과 수:", len(results))

    for index, doc in enumerate(
        results,
        start=1,
    ):

        print("\n" + "=" * 70)
        print(f"검색 결과 {index}")
        print("=" * 70)

        print(
            "문서:",
            doc.metadata.get("document_name"),
        )

        print(
            "chunk_id:",
            doc.metadata.get("chunk_id"),
        )

        print(
            "chunk_no:",
            doc.metadata.get("chunk_no"),
        )

        print(
            "article_no:",
            doc.metadata.get("article_no"),
        )

        print(
            "appendix_no:",
            doc.metadata.get("appendix_no"),
        )

        print("\n내용:")
        print(doc.page_content)


def main():

    store = load_vector_store()

    print(
        "현재 Chroma 저장 개수:",
        store._collection.count(),
    )

    test_search(
        store=store,
        query="휴직 중 직무급 지급 기준은?",
        k=3,
    )


if __name__ == "__main__":
    main()