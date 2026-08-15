from langchain_upstage import UpstageDocumentParseLoader
import json
from dotenv import load_dotenv
from config import RAW_DIR, PARSED_DIR

load_dotenv()

def up_parser(path):
    loader = UpstageDocumentParseLoader(
        path,
        split='element',
        ocr="force"
    )
    parsed_docs = loader.load()
    return parsed_docs

def save_parsed_docs(parsed_docs, output_path):
    documents_data = []

    for doc in parsed_docs:
        doc_data = {
            'page_content': doc.page_content,
            'metadata': doc.metadata
        }
        documents_data.append(doc_data)

    # JSON 파일로 저장
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            documents_data,
            f,
            ensure_ascii=False,
            indent=2
        )

    # 저장 확인
    print(f"저장 완료: {output_path}")

if __name__ == "__main__":

    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    pdf_files = list(RAW_DIR.glob("*.pdf"))

    for pdf_path in pdf_files:
        print(f"파싱 시작: {pdf_path.name}")
        parsed_docs = up_parser(pdf_path)
        output_path = PARSED_DIR / f"{pdf_path.stem}.json"
        save_parsed_docs(parsed_docs, output_path)

    print("모든 PDF 파싱 완료")
