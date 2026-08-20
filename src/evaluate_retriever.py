import pandas as pd
import pandas as pd

from retriever import (
    load_vector_store,
    get_retriever,
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


scores_k3 = evaluate(3)
scores_k10 = evaluate(10)


print(
    "잰 문항 수:",
    len(scores_k3),
)


# K=3 질문별 상세 결과
detail = scores_k3.merge(
    evalset[
        ["query_id", "query"]
    ],
    on="query_id",
)

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


# K=3 평균
print("\nK = 3 평균")

print(
    scores_k3[
        ["Hit", "P", "R", "MRR"]
    ]
    .mean()
    .round(3)
    .to_string()
)


# K=3 / K=10 비교
compare = pd.DataFrame([
    {
        "K": 3,
        **scores_k3[
            ["Hit", "P", "R", "MRR"]
        ]
        .mean()
        .round(3)
        .to_dict(),
    },
    {
        "K": 10,
        **scores_k10[
            ["Hit", "P", "R", "MRR"]
        ]
        .mean()
        .round(3)
        .to_dict(),
    },
])

print("\nK 비교")

print(
    compare.to_string(
        index=False
    )
)