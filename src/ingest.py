import json

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

JSON_PATH = "data/processed/llama_parsed/전체_문서_chunks_normalized.json"
CHROMA_PATH = "chroma/ko-sroberta/"
COLLECTION_NAME = "company_regulations"
EMBEDDING_MODEL = "jhgan/ko-sroberta-multitask"

def load_chunks() -> list[dict]:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    return chunks


def make_documents(
    chunks: list[dict]
) -> tuple[list[Document], list[str]]:
    docs = []
    ids = []

    for chunk in chunks:

        page_content = chunk.get("page_content")

        if not page_content:
            continue

        chunk_id = chunk.get("chunk_id")

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
        }

        metadata = {
            key: value 
            for key, value in metadata.items() 
            if value is not None
        }

        doc = Document(
            page_content=page_content,
            metadata=metadata
        )

        docs.append(doc)
        ids.append(chunk_id)

    return docs, ids

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

def create_vector_store(
        docs: list[Document],
        ids: list[str],
        embeddings,
        ) -> Chroma:
    store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        ids=ids,
        persist_directory=CHROMA_PATH,
    )

    return store

def main() -> None:

    # json 로드
    chunks = load_chunks()

    print("원본 chunk 수:", len(chunks))

    # langchain Document 생성
    docs, ids = make_documents(chunks)

    print("\nDocument 수:", len(docs))
    print("ID 수:", len(ids))

    embeddings = get_embeddings()

    store = create_vector_store(
        docs=docs,
        ids=ids,
        embeddings=embeddings,
    )

    stored_count = store._collection.count()

if __name__ == "__main__":
    main()
