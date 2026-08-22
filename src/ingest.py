import json
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


# =========================================================
# 경로 설정
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

JSON_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "llama_parsed"
    / "전체_문서_chunks_normalized.json"
)

CHROMA_PATH = (
    PROJECT_ROOT
    / "chroma"
    / "ko-sroberta"
)

COLLECTION_NAME = "company_regulations"

EMBEDDING_MODEL = "jhgan/ko-sroberta-multitask"


# =========================================================
# Chunk JSON 로드
# =========================================================

def load_chunks() -> list[dict]:

    if not JSON_PATH.exists():
        raise FileNotFoundError(
            f"정규화 Chunk JSON을 찾을 수 없습니다: {JSON_PATH}"
        )

    with JSON_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:

        chunks = json.load(f)

    return chunks


# =========================================================
# LangChain Document 생성
# =========================================================

def make_documents(
    chunks: list[dict],
) -> tuple[list[Document], list[str]]:

    docs = []
    ids = []

    for chunk in chunks:

        page_content = chunk.get(
            "page_content"
        )

        if not page_content:
            continue

        chunk_id = chunk.get(
            "chunk_id"
        )

        if not chunk_id:
            continue

        metadata = {
            "document_name": chunk.get("document_name"),
            "chunk_id": chunk.get("chunk_id"),
            "chunk_no": chunk.get("chunk_no"),
            "source_file": chunk.get("source_file"),
            "section_type": chunk.get("section_type"),
            "chunk_type": chunk.get("chunk_type"),
            "chapter": chunk.get("chapter"),
            "article_no": chunk.get("article_no"),
            "article_title": chunk.get("article_title"),
            "paragraph": chunk.get("paragraph"),
            "appendix_no": chunk.get("appendix_no"),
            "appendix_title": chunk.get("appendix_title"),
            "subsection": chunk.get("subsection"),
            "related_article": chunk.get("related_article"),
        }

        metadata = {
            key: value
            for key, value in metadata.items()
            if value is not None
        }

        doc = Document(
            page_content=page_content,
            metadata=metadata,
        )

        docs.append(doc)
        ids.append(chunk_id)

    return docs, ids


# =========================================================
# Embedding
# =========================================================

def get_embeddings():

    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={
            "device": "cpu",
        },
        encode_kwargs={
            "normalize_embeddings": True,
        },
    )


# =========================================================
# Vector DB 생성
# =========================================================

def create_vector_store(
    embeddings,
) -> Chroma:

    chunks = load_chunks()

    docs, ids = make_documents(
        chunks
    )

    if not docs:
        raise RuntimeError(
            "Vector DB에 저장할 Document가 없습니다."
        )

    CHROMA_PATH.mkdir(
        parents=True,
        exist_ok=True,
    )

    store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        ids=ids,
        persist_directory=str(CHROMA_PATH),
    )

    return store


# =========================================================
# Chroma 존재 여부 확인
# =========================================================

def chroma_exists() -> bool:

    sqlite_path = (
        CHROMA_PATH
        / "chroma.sqlite3"
    )

    return sqlite_path.exists()


# =========================================================
# 로컬 ingest 실행
# =========================================================

def main():

    embeddings = get_embeddings()

    store = create_vector_store(
        embeddings=embeddings,
    )

    stored_count = (
        store._collection.count()
    )

    print(
        f"Chroma 저장 완료: {stored_count}개"
    )


if __name__ == "__main__":
    main()