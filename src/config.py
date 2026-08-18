from pathlib import Path

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 데이터 경로
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# LlamaParse 결과
LLAMA_PARSED_DIR = PROCESSED_DIR / "llama_parsed"
PARSED_DIR = LLAMA_PARSED_DIR / "parsed"
CHUNK_DIR = LLAMA_PARSED_DIR / "chunks"
ALL_CHUNKS_PATH = LLAMA_PARSED_DIR / "전체_문서_chunks.json"
