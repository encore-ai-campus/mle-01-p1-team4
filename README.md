# mle-01-p1-team4
LX 사내문서 RAG 챗봇 &amp; 대시보드
# Lxpert

> 한 줄 소개: 한국국토정보공사(LX)의 사내 규정 문서를 전처리·임베딩하여  
> 사용자의 질문과 관련된 규정을 검색하고, **근거 문서와 함께 답변하는 RAG 챗봇**과  
> **검색·질문 임베딩 분석 대시보드**를 하나의 Streamlit 앱으로 제공합니다.

🔗 데모: ((https://mle-01-p1-team4-85shjgm8vqx98akldf2s46.streamlit.app/)) 
📊 발표자료: (링크)
📓 팀 노션: (https://app.notion.com/p/3b5fceb573c38114a20ecfe6ea86b228)

---

## 1. 프로젝트 소개

- **문제**: 사내 규정이 여러 PDF에 분산되어 있어 직원이 필요한 조항을 찾기 어렵고, 규정을 잘 모르는 경우 인사 담당 부서에 반복적으로 문의해야 합니다.
담당자 역시 규정 확인과 반복 답변에 시간이 소요되어 직원과 담당 부서 모두 업무 효율이 저하됩니다.
- **해결**: 사내 규정을 조·항·별표 단위로 청킹하고 ChromaDB에 저장해, 직원이 자연어 질문으로 필요한 규정을 빠르게 검색하도록 구현했습니다.
RAG 챗봇이 근거 규정과 출처를 함께 제공하고, 원문 조회·담당 부서 안내·분석 대시보드 기능을 하나의 Streamlit 앱에서 제공합니다.
- **기간 / 팀**: 2026.08.20 ~ 2026.08.24 (3일) / 3명

## 2. 데모

| 홈 | 분석 대시보드 1 |
| --- | --- |
| ![home](docs/images/home1.png) | ![dashboard1](docs/images/home2.png) |

| 분석 대시보드 2 | RAG 규정 챗봇 |
| ![dashboard2](docs/images/chatbot1.png) | ![chatbot](docs/images/chatbot2.png) |

| 데이터 분석 |
| --- |
| ![analysis](docs/images/analysis.png) |
## 3. 주요 기능

### 규정 정보 대시보드
- 지도 기반 규정 및 담당 부서 정보 제공
- 규정 PDF별 원문 조회
- 직원들이 자주 묻는 질문 Top 5 제공
- Golden Set 질문 임베딩 분석
- Retriever 및 LLM 응답시간 비교

### 근거 기반 RAG 챗봇
- 사용자의 자연어 질문과 관련된 규정 검색
- 검색된 규정만 Context로 사용해 답변 생성
- 답변마다 실제 참고한 문서명·조문·별표 표시
- 근거를 찾지 못하면 관련 내용을 확인할 수 없다고 안내
- 대화 내용에 맞는 후속 추천 질문 제공
- 답변마다 랜디 캐릭터 이미지를 무작위로 표시

### 규정 문서 구조 반영
- 장·조·항 단위로 규정 본문 분할
- 일반 조문과 별표를 구분해 metadata 저장
- 조문에서 참조하는 관련 별표까지 검색 범위 확장
- 검색된 Chunk의 주변 문맥을 함께 조회
- 동일한 규정 출처가 반복되지 않도록 중복 제거

### 검색 품질 평가
- 정답 Chunk를 지정한 Golden Set 구축
- Hit@K, Precision@K, Recall@K, MRR 측정
- K값에 따른 검색 성능 비교
- 검색 정확도와 검색 문서 수 사이의 Trade-off 분석


## 4. 아키텍처

(mermaid 다이어그램 — 아래 스니펫 참고)

## 5. 기술 스택 -> 팀장님 드리기

| 구분 | 사용 기술 |
| --- | --- |
| 언어 / 환경 | Python 3.11, uv |
| 데이터 | pandas, scipy, scikit-learn |
| LLM / 임베딩 | OpenAI GPT (모델명 명시) |
| RAG | LangChain, ChromaDB |
| 앱 | Streamlit, Plotly |
| 협업 | GitHub (브랜치 · PR · 리뷰), Notion, FigJam |

## 6. 데이터 -> 팀장님 드리기

- **출처**: OO 공공데이터 API — (링크)
- **수집 기간 / 건수**: 2024-01 ~ 2025-12 / 원본 12,431건 → 전처리 후 11,208건
- **주요 컬럼**: (컬럼명 · 타입 · 의미 5개 내외)
- **전처리 요약**
  - 결측: (컬럼)의 결측 3.2% → (처리 방법)
  - 중복: 공고번호 기준 412건 제거
  - 이상치: (기준과 처리 방법)
  - 도메인 사전: "믹스 / 잡종 / 믹스견" → "믹스" 등 00개 용어 통일
- **상세 명세**: [데이터 명세서](docs/data_spec.md) · [전처리 명세서](docs/preprocess_spec.md)

## 7. 실행 방법 -> 빼두고

### 사전 준비

- Python 3.12, [uv](https://docs.astral.sh/uv/)
- OpenAI API Key ([발급](https://platform.openai.com/api-keys))

### 설치

    git clone https://github.com/ORG/REPO.git
    cd REPO
    uv sync

### 환경 변수

`.env.example`을 복사해 `.env`를 만들고 키를 채웁니다. `.env`는 커밋하지 않습니다.

    OPENAI_API_KEY=your_key_here

### 수집 → 인덱싱 → 실행

    uv run python src/collect.py      # 1) API 수집      → data/raw/
    uv run python src/preprocess.py   # 2) 전처리        → data/processed/
    uv run python src/index.py        # 3) 임베딩·적재   → chroma_db/  (약 3분)
    uv run streamlit run app.py       # 4) 앱 실행       → http://localhost:8501

## 8. 프로젝트 구조

    REPO/
    ├── app.py                  # Streamlit 통합 앱 (대시보드 + 챗봇)
    ├── src/
    │   ├── collect.py          # M1 API 수집
    │   ├── preprocess.py       # M2 전처리 · 도메인 사전
    │   ├── index.py            # M4 청킹 · 임베딩 · ChromaDB 적재
    │   ├── rag_chain.py        # M5 검색 → 생성 → 출처
    │   └── evaluate.py         # M6 Hit@K · MRR 측정
    ├── notebooks/              # M3 EDA · 통계 검정 (1인 1파일)
    ├── data/
    │   ├── raw/                # 원본 (커밋 제외)
    │   └── processed/          # 전처리 결과
    ├── eval/questions.json     # 평가셋 (질문 + 정답 문서)
    ├── docs/                   # 명세서 · 이미지 · 평가 리포트
    ├── .env.example
    └── README.md

## 9. 검색 품질 평가

평가셋: 정답 문서를 지정한 질문 30개 (`eval/questions.json`)

| 실험 | Hit@5 | Precision@5 | MRR | 비고 |
| --- | --- | --- | --- | --- |
| Before (기본 설정) | 0.63 | 0.31 | 0.44 | chunk 1000 / overlap 0, top-k 5 |
| After (개선) | 0.80 | 0.42 | 0.61 | chunk 500 / overlap 100 |

**개선 실험(M7)**: (무엇이 문제였는지 → 무엇을 바꿨는지 → 왜 좋아졌다고 보는지 2~3줄)

재현: `uv run python src/evaluate.py`

## 10. 팀 소개

| 이름 | 역할 | 담당 | GitHub |
| --- | --- | --- | --- |
| 000 | PM | M0 기획 · 일정 · M9 시연 | @id |
| 000 | 데이터 | M1 수집 · M2 전처리 · M3 분석 | @id |
| 000 | RAG | M4 적재 · M5 체인 · M6·M7 평가 | @id |
| 000 | 대시보드 | M8 통합 앱 · 시각화 | @id |

## 11. 회고 (KPT)

- **Keep**: (계속 가져갈 것)
- **Problem**: (막혔던 지점과 원인)
- **Try**: (다음에 시도할 것)

상세 회고 → (팀 노션 링크)