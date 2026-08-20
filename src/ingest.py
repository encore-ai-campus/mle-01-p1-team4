import json

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

JSON_PATH = "data/processed/llama_parsed/전체_문서_chunks_normalized.json"
CHROMA_PATH = "chroma/ko-sroberta/"
COLLECTION_NAME = "company_regulations"
EMBEDDING_MODEL = "jhgan/ko-sroberta-multitask"


with open(JSON_PATH, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print("원본 chunk 수:", len(chunks))
print("첫 번째 chunk:", chunks[0])


docs = []

for chunk in chunks:

    page_content = chunk["content"]

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

    metadata = {key: value for key, value in metadata.items() if value is not None}

    doc = Document(page_content=page_content, metadata=metadata)

    docs.append(doc)


print("Document 수:", len(docs))
print("첫 번째 Document:", docs[0])


embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


ids = [chunk["chunk_id"] for chunk in chunks]


store = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    collection_name=COLLECTION_NAME,
    ids=ids,
    persist_directory=CHROMA_PATH,
)
