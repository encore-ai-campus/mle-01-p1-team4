from pathlib import Path

from dotenv import load_dotenv


# =========================================================
# 프로젝트 루트
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# =========================================================
# 환경 변수
# =========================================================

ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)


# =========================================================
# 데이터 경로
# =========================================================

DATA_DIR = PROJECT_ROOT / "data"

RAW_DIR = DATA_DIR / "raw"

PROCESSED_DIR = DATA_DIR / "processed"

LLAMA_PARSED_DIR = PROCESSED_DIR / "llama_parsed"

PARSED_DIR = LLAMA_PARSED_DIR / "parsed"

CHUNK_DIR = LLAMA_PARSED_DIR / "chunks"


# =========================================================
# Chunk JSON
# =========================================================

SOURCE_CHUNKS_PATH = (
    LLAMA_PARSED_DIR
    / "전체_문서_chunks.json"
)

NORMALIZED_CHUNKS_PATH = (
    LLAMA_PARSED_DIR
    / "전체_문서_chunks_normalized.json"
)

ALL_CHUNKS_PATH = SOURCE_CHUNKS_PATH


# =========================================================
# Vector DB
# =========================================================

CHROMA_DIR = PROJECT_ROOT / "chroma"

CHROMA_PATH = (
    CHROMA_DIR
    / "ko-sroberta"
)

COLLECTION_NAME = "company_regulations"

EMBEDDING_MODEL = (
    "jhgan/ko-sroberta-multitask"
)


# =========================================================
# 평가
# =========================================================

EVALUATION_DIR = PROJECT_ROOT / "evaluation"

GOLDEN_SET_PATH = (
    EVALUATION_DIR
    / "golden_set.csv"
)

EVALUATION_RESULT_DIR = (
    EVALUATION_DIR
    / "results"
)


# =========================================================
# Assets
# =========================================================

ASSET_DIR = PROJECT_ROOT / "assets"