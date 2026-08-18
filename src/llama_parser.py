import json
import os
import time
from pathlib import Path

import requests


llama_key = os.getenv("LLAMA_CLOUD_API_KEY")
LLAMA_BASE = "https://api.cloud.llamaindex.ai"

if not llama_key:
    raise RuntimeError(
        "LLAMA_CLOUD_API_KEY를 찾지 못했습니다.\n"
        "상위 폴더의 .env 파일과 load_dotenv 실행 여부를 확인하세요."
    )

head = {
    "Authorization": f"Bearer {llama_key}"
}


# 입력 폴더
PDF_DIR = Path("data2")

# 결과 저장 폴더
OUT_DIR = Path("output")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# data2 폴더 안의 PDF 목록
PDF_PATHS = sorted(PDF_DIR.glob("*.pdf"))

if not PDF_PATHS:
    raise FileNotFoundError(
        f"PDF 파일이 없습니다: {PDF_DIR.resolve()}"
    )

print(f"총 {len(PDF_PATHS)}개의 PDF를 처리합니다.")


for number, SAMPLE_PDF_PATH in enumerate(PDF_PATHS, start=1):
    print()
    print("=" * 60)
    print(f"[{number}/{len(PDF_PATHS)}] {SAMPLE_PDF_PATH.name}")
    print("=" * 60)

    try:
        # ---------------------------------------------
        # 1. 현재 PDF 업로드
        # ---------------------------------------------
        print("1. 파일 업로드 중...")

        with open(SAMPLE_PDF_PATH, "rb") as fp:
            up = requests.post(
                f"{LLAMA_BASE}/api/v1/beta/files",
                headers=head,
                files={
                    "file": (
                        SAMPLE_PDF_PATH.name,
                        fp,
                        "application/pdf",
                    )
                },
                data={"purpose": "parse"},
                timeout=120,
            )

        if not up.ok:
            raise RuntimeError(
                f"업로드 실패({up.status_code}): "
                f"{up.text[:300]}"
            )

        file_id = up.json()["id"]
        print(f"   업로드 완료 → file_id: {file_id}")


        # ---------------------------------------------
        # 2. 파싱 작업 생성
        # ---------------------------------------------
        print("2. 파싱 작업 생성 중...")

        job_response = requests.post(
            f"{LLAMA_BASE}/api/v2/parse",
            headers=head,
            json={
                "file_id": file_id,
                "tier": "cost_effective",
                "version": "latest",
            },
            timeout=120,
        )

        if not job_response.ok:
            raise RuntimeError(
                f"파싱 작업 생성 실패({job_response.status_code}): "
                f"{job_response.text[:300]}"
            )

        job_id = job_response.json()["id"]
        print(f"   작업 생성 완료 → job_id: {job_id}")


        # ---------------------------------------------
        # 3. 파싱 완료까지 기다리기
        # ---------------------------------------------
        print("3. 파싱 완료 대기 중...")

        result = None

        for attempt in range(120):
            result_response = requests.get(
                f"{LLAMA_BASE}/api/v2/parse/{job_id}",
                headers=head,
                params={"expand": "markdown"},
                timeout=120,
            )

            if not result_response.ok:
                raise RuntimeError(
                    f"상태 확인 실패({result_response.status_code}): "
                    f"{result_response.text[:300]}"
                )

            result = result_response.json()
            status = result.get("job", {}).get("status")

            print(
                f"   상태 확인 {attempt + 1}/120: {status}"
            )

            if status == "COMPLETED":
                break

            if status in {
                "FAILED",
                "ERROR",
                "CANCELLED",
                "CANCELED",
            }:
                raise RuntimeError(
                    f"파싱 작업 실패: {status}"
                )

            time.sleep(5)

        else:
            raise TimeoutError(
                "파싱이 10분 안에 완료되지 않았습니다."
            )


        # ---------------------------------------------
        # 4. Markdown 결과 꺼내기
        # ---------------------------------------------
        pages = result.get("markdown", {}).get("pages", [])

        if not pages:
            raise RuntimeError(
                "파싱 결과에 Markdown 페이지가 없습니다."
            )

        markdown_parts = []

        for page in pages:
            page_number = page.get("page_number", "알 수 없음")
            page_text = page.get("markdown", "")

            markdown_parts.append(
                f"<!-- page: {page_number} -->\n\n"
                f"{page_text}"
            )

        full_markdown = "\n\n".join(markdown_parts)


        # ---------------------------------------------
        # 5. 현재 PDF 이름으로 결과 저장
        # ---------------------------------------------
        markdown_path = (
            OUT_DIR / f"{SAMPLE_PDF_PATH.stem}_파싱결과.md"
        )

        json_path = (
            OUT_DIR / f"{SAMPLE_PDF_PATH.stem}_파싱결과.json"
        )

        markdown_path.write_text(
            full_markdown,
            encoding="utf-8",
        )

        json_path.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print("4. 저장 완료")
        print(f"   페이지 수: {len(pages)}")
        print(f"   Markdown: {markdown_path}")
        print(f"   JSON: {json_path}")


    except Exception as error:
        # 한 PDF가 실패해도 다음 PDF는 계속 처리
        print("처리 실패")
        print(f"   파일: {SAMPLE_PDF_PATH.name}")
        print(f"   원인: {error}")


print()
print("모든 PDF 처리가 끝났습니다.")

import re


CHAPTER_PATTERN = re.compile(
    r"(?m)^[ \t]*#{0,6}[ \t]*("
    r"제\s*\d+\s*장"
    r"(?:\s+[^\n]+)?"
    r")"
)


ARTICLE_PATTERN = re.compile(
    r"(?m)^[ \t]*#{0,6}[ \t]*("
    r"제\s*\d+\s*조"
    r"(?:의\s*\d+)?"
    r"(?:\s*\([^)\n]+\))?"
    r")"
)


PARAGRAPH_PATTERN = re.compile(
    r"[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]"
)

import json
from pathlib import Path


# LlamaParse JSON 파일이 들어 있는 폴더
PARSED_DIR = Path("output")

# 청킹 결과를 저장할 폴더
CHUNK_DIR = Path("output/chunks")
CHUNK_DIR.mkdir(parents=True, exist_ok=True)


# 파싱 결과 JSON 목록
json_paths = sorted(
    PARSED_DIR.glob("*_파싱결과.json")
)

if not json_paths:
    raise FileNotFoundError(
        f"파싱 결과 JSON이 없습니다: {PARSED_DIR.resolve()}"
    )


all_document_chunks = []
processing_summary = []


for number, json_path in enumerate(json_paths, start=1):
    print()
    print("=" * 60)
    print(f"[{number}/{len(json_paths)}] {json_path.name}")
    print("=" * 60)

    try:
        # ------------------------------------------
        # 1. LlamaParse JSON 읽기
        # ------------------------------------------
        result = json.loads(
            json_path.read_text(encoding="utf-8")
        )


        # ------------------------------------------
        # 2. 페이지 목록 꺼내기
        # ------------------------------------------
        pages = (
            result.get("markdown", {})
            .get("pages", [])
        )

        if not pages:
            raise RuntimeError(
                "JSON에 markdown.pages가 없습니다."
            )


        # ------------------------------------------
        # 3. 모든 페이지를 순서대로 연결
        # ------------------------------------------
        document_text = "\n\n".join(
            page.get("markdown", "")
            for page in pages
            if page.get("markdown")
        )

        if not document_text.strip():
            raise RuntimeError(
                "페이지의 Markdown 내용이 비어 있습니다."
            )


        # ------------------------------------------
        # 4. 파일명에서 문서명 만들기
        # ------------------------------------------
        document_name = json_path.stem

        document_name = document_name.removesuffix(
            "_파싱결과"
        )


        # ------------------------------------------
        # 5. 장 → 조 → 항 청킹
        # ------------------------------------------
        chunks = split_legal_document(
            document_text=document_text,
            document_name=document_name,
        )


        if not chunks:
            raise RuntimeError(
                "장·조·항 패턴에 맞는 청크를 만들지 못했습니다."
            )


        # ------------------------------------------
        # 6. 청크마다 고유 ID 추가
        # ------------------------------------------
        for chunk_index, chunk in enumerate(
            chunks,
            start=1,
        ):
            chunk["chunk_id"] = (
                f"{document_name}_{chunk_index:04d}"
            )

            chunk["source_file"] = json_path.name


        # ------------------------------------------
        # 7. 문서별 청크 JSON 저장
        # ------------------------------------------
        chunk_path = (
            CHUNK_DIR
            / f"{document_name}_chunks.json"
        )

        chunk_path.write_text(
            json.dumps(
                chunks,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


        # 전체 통합 목록에도 추가
        all_document_chunks.extend(chunks)

        processing_summary.append({
            "document_name": document_name,
            "status": "성공",
            "pages": len(pages),
            "chunks": len(chunks),
            "output": str(chunk_path),
        })

        print("처리 성공")
        print("문서명:", document_name)
        print("페이지 수:", len(pages))
        print("청크 수:", len(chunks))
        print("저장 위치:", chunk_path)


    except Exception as error:
        processing_summary.append({
            "document_name": json_path.stem,
            "status": "실패",
            "error": str(error),
        })

        print("처리 실패")
        print("원인:", error)

ALL_CHUNKS_PATH = (
    CHUNK_DIR / "전체_문서_chunks.json"
)

ALL_CHUNKS_PATH.write_text(
    json.dumps(
        all_document_chunks,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print()
print("=" * 60)
print("전체 처리 완료")
print("처리한 JSON:", len(json_paths), "개")
print("전체 청크:", len(all_document_chunks), "개")
print("통합 결과:", ALL_CHUNKS_PATH.resolve())

from pathlib import Path

ALL_CHUNKS_PATH = Path(
    "output/chunks/전체_문서_chunks.json"
)

print("저장 위치:", ALL_CHUNKS_PATH.resolve())
print("파일 존재 여부:", ALL_CHUNKS_PATH.exists())