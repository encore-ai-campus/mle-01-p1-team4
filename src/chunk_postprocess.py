import json

from config import NORMALIZED_CHUNKS_PATH, SOURCE_CHUNKS_PATH
from legal_chunking import postprocess_chunks


def load_chunks() -> list[dict]:
    if not SOURCE_CHUNKS_PATH.exists():
        raise FileNotFoundError(
            f"입력 파일을 찾을 수 없습니다: {SOURCE_CHUNKS_PATH.resolve()}"
        )

    try:
        chunks = json.loads(SOURCE_CHUNKS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"JSON 형식이 올바르지 않습니다: {SOURCE_CHUNKS_PATH.resolve()}"
        ) from exc

    if not isinstance(chunks, list):
        raise TypeError("전체_문서_chunks.json의 최상위 값은 list여야 합니다.")

    return chunks


def save_chunks(chunks: list[dict]) -> None:
    NORMALIZED_CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    NORMALIZED_CHUNKS_PATH.write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    source_chunks = load_chunks()
    normalized_chunks = postprocess_chunks(source_chunks)
    save_chunks(normalized_chunks)

    print(f"입력 청크 수: {len(source_chunks)}")
    print(f"출력 청크 수: {len(normalized_chunks)}")
    print(f"저장 위치: {NORMALIZED_CHUNKS_PATH.resolve()}")


if __name__ == "__main__":
    main()
