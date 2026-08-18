from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LLAMA_PARSED_DIR = PROCESSED_DIR / "llama_parsed"

SOURCE_CHUNKS_PATH = LLAMA_PARSED_DIR / "전체_문서_chunks.json"
NORMALIZED_CHUNKS_PATH = LLAMA_PARSED_DIR / "전체_문서_chunks_normalized.json"
