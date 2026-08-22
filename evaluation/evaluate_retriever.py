import pandas as pd
import pandas as pd
from pathlib import Path

from src.rag.retriever import (
    load_vector_store,
    get_retriever,
)

RESULT_DIR = Path("evaluation/results")
RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

EVALSET_PATH = "evaluation/golden_set.csv"

evalset = pd.read_csv(
    EVALSET_PATH,
    encoding="utf-8",
)

def hit_at_k(predicted, relevant, k):
    """상위 k개 중 정답이 하나라도 있으면 1, 없으면 0."""
    return 1 if any(p in relevant for p in predicted[:k]) else 0


def precision_at_k(predicted, relevant, k):
    """상위 k개 중 정답의 비율(정답 개수 / k)."""
    return sum(1 for p in predicted[:k] if p in relevant) / k


def recall_at_k(predicted, relevant, k):
    """전체 정답 중 상위 k개가 건진 비율(찾은 정답 수 / 전체 정답 수)."""
    return sum(1 for p in predicted[:k] if p in relevant) / len(relevant)


def mrr_at_k(predicted, relevant, k):
    """첫 정답 순위의 역수(1위면 1, 2위면 0.5 ...). 상위 k개 안에 없으면 0."""
    for rank, p in enumerate(predicted[:k], 1):
        if p in relevant:
            # 처음 만난 정답에서 바로 끝낸다
            return 1 / rank
    return 0.0
    
# 라벨을 '문항 id -> 정답 조각 목록' 사전으로 만듦
gold_map = {row.query_id: row.gold_chunks.split('|') for row in evalset.itertuples()}

store = load_vector_store()

def evaluate(k):
    rows = []

    retriever = get_retriever(
        store=store,
        k=k,
    )

    for row in evalset.itertuples():

        results = retriever.invoke(
            row.query
        )

        predicted = [
            doc.metadata["chunk_id"]
            for doc in results
        ]

        relevant = gold_map[
            row.query_id
        ]

        rows.append({
            "query_id": row.query_id,
            "Hit": hit_at_k(
                predicted,
                relevant,
                k,
            ),
            "P": precision_at_k(
                predicted,
                relevant,
                k,
            ),
            "R": recall_at_k(
                predicted,
                relevant,
                k,
            ),
            "MRR": mrr_at_k(
                predicted,
                relevant,
                k,
            ),
        })

    return pd.DataFrame(rows)

scores_by_k = {}
compare_rows = []

for k in range(3, 11):
    # 현재 K값으로 평가
    scores = evaluate(k)

    # K별 평가 결과 보관
    scores_by_k[k] = scores

    # 질문 내용 추가
    detail = scores.merge(
        evalset[
            ["query_id", "query"]
        ],
        on="query_id",
    )

    # K별 상세 결과 출력
    print(f"\nK = {k} 질문별 상세 결과")

    print(
        detail[
            [
                "query_id",
                "Hit",
                "P",
                "R",
                "MRR",
                "query",
            ]
        ].round(3)
    )
    # K별 상세 결과 저장
    detail.to_csv(
        RESULT_DIR / f"retriever_k{k}_detail.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # 현재 K의 평균 점수
    average_scores = (
        scores[
            ["Hit", "P", "R", "MRR"]
        ]
        .mean()
        .round(3)
    )

    print(f"\nK = {k} 평균")
    print(average_scores.to_string())

    # K별 평균 비교표에 추가
    compare_rows.append({
        "K": k,
        **average_scores.to_dict(),
    })


# K=3부터 K=10까지 평균 비교표
compare = pd.DataFrame(compare_rows)

print("\nK 비교")
print(
    compare.to_string(
        index=False
    )
)

# 평균 비교표 저장
compare.to_csv(
    RESULT_DIR / "retriever_k_compare.csv",
    index=False,
    encoding="utf-8-sig",
)

print(
    "\n평가한 문항 수:",
    len(evalset),
)

print(
    "평가한 K값 수:",
    len(scores_by_k),
)