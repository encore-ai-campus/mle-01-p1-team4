from pathlib import Path


# 프로젝트 루트
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# 데이터 경로
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
PARSED_DIR = PROCESSED_DIR / "parsed"