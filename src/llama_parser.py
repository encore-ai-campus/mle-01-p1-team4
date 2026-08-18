import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from config import (
    PROJECT_ROOT,
    RAW_DIR,
    PARSED_DIR,
    CHUNK_DIR,
    ALL_CHUNKS_PATH,
)
from legal_chunking import split_legal_document

LLAMA_BASE = "https://api.cloud.llamaindex.ai"
REQUEST_TIMEOUT = 120
POLL_INTERVAL_SECONDS = 5
MAX_POLL_ATTEMPTS = 120


def get_headers() -> dict[str, str]:
    load_dotenv(PROJECT_ROOT / ".env")
    llama_key = os.getenv("LLAMA_CLOUD_API_KEY")
    if not llama_key:
        raise RuntimeError(
            "LLAMA_CLOUD_API_KEY를 찾지 못했습니다. "
            "프로젝트 루트의 .env 파일을 확인하세요."
        )
    return {"Authorization": f"Bearer {llama_key}"}


def parse_pdf(pdf_path: Path, headers: dict[str, str]) -> dict:
    """PDF 1개를 LlamaParse에 전송하고 완료된 결과 JSON을 반환한다."""
    with pdf_path.open("rb") as fp:
        upload_response = requests.post(
            f"{LLAMA_BASE}/api/v1/beta/files",
            headers=headers,
            files={"file": (pdf_path.name, fp, "application/pdf")},
            data={"purpose": "parse"},
            timeout=REQUEST_TIMEOUT,
        )

    if not upload_response.ok:
        raise RuntimeError(
            f"업로드 실패({upload_response.status_code}): "
            f"{upload_response.text[:300]}"
        )

    file_id = upload_response.json()["id"]

    job_response = requests.post(
        f"{LLAMA_BASE}/api/v2/parse",
        headers=headers,
        json={
            "file_id": file_id,
            "tier": "cost_effective",
            "version": "latest",
        },
        timeout=REQUEST_TIMEOUT,
    )

    if not job_response.ok:
        raise RuntimeError(
            f"파싱 작업 생성 실패({job_response.status_code}): "
            f"{job_response.text[:300]}"
        )

    job_id = job_response.json()["id"]

    for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
        result_response = requests.get(
            f"{LLAMA_BASE}/api/v2/parse/{job_id}",
            headers=headers,
            params={"expand": "markdown"},
            timeout=REQUEST_TIMEOUT,
        )

        if not result_response.ok:
            raise RuntimeError(
                f"상태 확인 실패({result_response.status_code}): "
                f"{result_response.text[:300]}"
            )

        result = result_response.json()
        status = result.get("job", {}).get("status")
        print(f"   상태 확인 {attempt}/{MAX_POLL_ATTEMPTS}: {status}")

        if status == "COMPLETED":
            return result

        if status in {"FAILED", "ERROR", "CANCELLED", "CANCELED"}:
            raise RuntimeError(f"파싱 작업 실패: {status}")

        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError("파싱이 제한 시간 안에 완료되지 않았습니다.")


def save_parse_result(pdf_path: Path, result: dict) -> tuple[Path, Path]:
    pages = result.get("markdown", {}).get("pages", [])
    if not pages:
        raise RuntimeError("파싱 결과에 Markdown 페이지가 없습니다.")

    markdown_parts = []
    for page in pages:
        page_number = page.get("page_number", "알 수 없음")
        page_text = page.get("markdown", "")
        markdown_parts.append(
            f"<!-- page: {page_number} -->\n\n{page_text}"
        )

    full_markdown = "\n\n".join(markdown_parts)
    markdown_path = PARSED_DIR / f"{pdf_path.stem}_파싱결과.md"
    json_path = PARSED_DIR / f"{pdf_path.stem}_파싱결과.json"

    markdown_path.write_text(full_markdown, encoding="utf-8")
    json_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return markdown_path, json_path


def parse_all_pdfs() -> None:
    pdf_paths = sorted(RAW_DIR.glob("*.pdf"))
    if not pdf_paths:
        raise FileNotFoundError(f"PDF 파일이 없습니다: {RAW_DIR.resolve()}")

    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    headers = get_headers()

    print(f"총 {len(pdf_paths)}개의 PDF를 처리합니다.")

    for number, pdf_path in enumerate(pdf_paths, start=1):
        print("\n" + "=" * 60)
        print(f"[{number}/{len(pdf_paths)}] {pdf_path.name}")
        print("=" * 60)

        try:
            result = parse_pdf(pdf_path, headers)
            markdown_path, json_path = save_parse_result(pdf_path, result)
            print("파싱 저장 완료")
            print("   Markdown:", markdown_path)
            print("   JSON:", json_path)
        except Exception as error:
            # 한 PDF가 실패해도 나머지는 계속 처리한다.
            print("처리 실패")
            print("   파일:", pdf_path.name)
            print("   원인:", error)


def extract_document_text(result: dict) -> tuple[str, int]:
    pages = result.get("markdown", {}).get("pages", [])
    if not pages:
        raise RuntimeError("JSON에 markdown.pages가 없습니다.")

    document_text = "\n\n".join(
        page.get("markdown", "")
        for page in pages
        if page.get("markdown")
    )
    if not document_text.strip():
        raise RuntimeError("페이지의 Markdown 내용이 비어 있습니다.")

    return document_text, len(pages)


def build_chunks_from_parsed_json() -> None:
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)

    json_paths = sorted(PARSED_DIR.glob("*.json"))
    if not json_paths:
        raise FileNotFoundError(
            f"파싱 결과 JSON이 없습니다: {PARSED_DIR.resolve()}"
        )

    all_document_chunks = []

    for number, json_path in enumerate(json_paths, start=1):
        print("\n" + "=" * 60)
        print(f"[{number}/{len(json_paths)}] {json_path.name}")
        print("=" * 60)

        try:
            result = json.loads(json_path.read_text(encoding="utf-8"))
            document_text, page_count = extract_document_text(result)
            document_name = json_path.stem.removesuffix("_파싱결과")

            chunks = split_legal_document(
                document_text=document_text,
                document_name=document_name,
            )
            if not chunks:
                raise RuntimeError("규정 구조에 맞는 청크를 만들지 못했습니다.")

            for chunk_index, chunk in enumerate(chunks, start=1):
                chunk["chunk_id"] = f"{document_name}_{chunk_index:04d}"
                chunk["source_file"] = json_path.name

            chunk_path = CHUNK_DIR / f"{document_name}_chunks.json"
            chunk_path.write_text(
                json.dumps(chunks, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            all_document_chunks.extend(chunks)
            print("청킹 성공")
            print("   문서명:", document_name)
            print("   페이지 수:", page_count)
            print("   청크 수:", len(chunks))
            print("   저장 위치:", chunk_path)

        except Exception as error:
            print("청킹 실패")
            print("   파일:", json_path.name)
            print("   원인:", error)

    ALL_CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ALL_CHUNKS_PATH.write_text(
        json.dumps(all_document_chunks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n" + "=" * 60)
    print("전체 청킹 완료")
    print("전체 청크:", len(all_document_chunks), "개")
    print("통합 결과:", ALL_CHUNKS_PATH.resolve())


def main() -> None:
    # 이미 LlamaParse 결과 JSON이 있다면 재파싱하지 않는다.
    # parse_all_pdfs()
    build_chunks_from_parsed_json()


if __name__ == "__main__":
    main()
